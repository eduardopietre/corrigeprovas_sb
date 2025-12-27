"""
Test for token balance race condition vulnerability.

This test attempts to exploit the race condition in the reserve_tokens function
where multiple concurrent requests could potentially bypass balance checks.
"""

import asyncio
import os
import uuid
from datetime import datetime

import pytest

from supabase import create_client


class TestTokenRaceCondition:
    """Test token balance race condition vulnerability."""
    
    @pytest.fixture
    def supabase_client(self):
        """Create Supabase client with service role for testing."""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            pytest.skip("Supabase credentials not available")
        return create_client(url, key)
    
    @pytest.fixture
    def test_user_id(self, supabase_client):
        """Create a test user with limited tokens."""
        user_id = str(uuid.uuid4())
        
        # Create profile
        supabase_client.table("profiles").insert({
            "user_id": user_id,
            "email": f"test-{user_id}@example.com"
        }).execute()
        
        # Give user 10 tokens
        supabase_client.rpc("credit_tokens", {
            "p_user_id": user_id,
            "p_amount": 10,
            "p_reason": "ADMIN_ADJUSTMENT"
        }).execute()
        
        yield user_id
        
        # Cleanup
        supabase_client.table("profiles").delete().eq("user_id", user_id).execute()
        supabase_client.table("usage_ledger").delete().eq("user_id", user_id).execute()
    
    async def attempt_token_reservation(self, supabase_client, user_id, amount, job_id):
        """Attempt to reserve tokens for a job."""
        try:
            result = supabase_client.rpc("reserve_tokens", {
                "p_user_id": user_id,
                "p_amount": amount,
                "p_job_id": job_id
            }).execute()
            return result.data
        except Exception as e:
            return False
    
    @pytest.mark.asyncio
    async def test_concurrent_token_reservation(self, supabase_client, test_user_id):
        """
        Test if concurrent token reservations can bypass balance checks.
        
        This test creates multiple concurrent requests to reserve tokens
        that would exceed the user's balance if processed simultaneously.
        """
        # Create multiple job IDs
        job_ids = [str(uuid.uuid4()) for _ in range(5)]
        
        # Attempt to reserve 8 tokens each (total 40, but user only has 10)
        tasks = [
            self.attempt_token_reservation(supabase_client, test_user_id, 8, job_id)
            for job_id in job_ids
        ]
        
        # Execute all reservations concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful reservations
        successful_reservations = sum(1 for result in results if result is True)
        
        # Check final balance
        balance_result = supabase_client.rpc("get_balance", {
            "p_user_id": test_user_id
        }).execute()
        final_balance = balance_result.data
        
        # VULNERABILITY: If more than 1 reservation succeeded, we have a race condition
        if successful_reservations > 1:
            pytest.fail(
                f"VULNERABILITY CONFIRMED: {successful_reservations} concurrent reservations "
                f"succeeded, but user only had 10 tokens. Final balance: {final_balance}"
            )
        
        # If only 1 or 0 succeeded, the protection is working
        assert successful_reservations <= 1, "Race condition protection failed"
        assert final_balance >= 0, "Balance went negative"
    
    def test_token_balance_calculation_accuracy(self, supabase_client, test_user_id):
        """
        Test if token balance calculation is accurate under normal conditions.
        """
        # Get initial balance
        initial_balance = supabase_client.rpc("get_balance", {
            "p_user_id": test_user_id
        }).execute().data
        
        # Reserve some tokens
        job_id = str(uuid.uuid4())
        reservation_result = supabase_client.rpc("reserve_tokens", {
            "p_user_id": test_user_id,
            "p_amount": 5,
            "p_job_id": job_id
        }).execute()
        
        # Check if reservation succeeded
        assert reservation_result.data is True, "Token reservation should succeed"
        
        # Check new balance
        new_balance = supabase_client.rpc("get_balance", {
            "p_user_id": test_user_id
        }).execute().data
        
        expected_balance = initial_balance - 5
        assert new_balance == expected_balance, f"Balance calculation incorrect: expected {expected_balance}, got {new_balance}"
    
    def test_insufficient_balance_protection(self, supabase_client, test_user_id):
        """
        Test if the system properly rejects reservations when balance is insufficient.
        """
        # Try to reserve more tokens than available
        job_id = str(uuid.uuid4())
        reservation_result = supabase_client.rpc("reserve_tokens", {
            "p_user_id": test_user_id,
            "p_amount": 50,  # User only has 10 tokens
            "p_job_id": job_id
        }).execute()
        
        # Should return False for insufficient balance
        assert reservation_result.data is False, "Should reject reservation with insufficient balance"
        
        # Balance should remain unchanged
        balance = supabase_client.rpc("get_balance", {
            "p_user_id": test_user_id
        }).execute().data
        
        assert balance == 10, f"Balance should remain 10, but got {balance}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])