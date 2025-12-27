import itertools
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass

import numpy as np
from tqdm import tqdm

from src.errors import UnableToFindFourAlignTrianglesException, FoundAlignTrianglesAreNotFilledException
from src.utils import relative_path
from src.recognizer import Recognizer
from src.template_matcher import TemplateData
from src.constants import TemplateName
from storage import lazy_iterate_dataset


def delegate_test(template: TemplateName, append: str, recognizer: Recognizer, huge: bool) -> (float, float, int):
    """
    Runs recognition on a Zarr dataset for the given template and append mode.
    Returns a tuple: (average_error, align_error_rate, total_amount).
    """
    total_amount = 0
    align_error = 0
    errors = 0

    if huge:
        path = relative_path(f"generated/synthetic_test_data_huge/{template.value}_{append}.zarr", __file__)
    else:
        path = relative_path(f"generated/synthetic_test_data/{template.value}_{append}.zarr", __file__)

    for images, labels in lazy_iterate_dataset(path, 50):
        total_amount += len(images)
        for i in range(len(images)):
            img = images[i]
            label = labels[i]

            try:
                correction_result = recognizer.correct(img, label)
            except (UnableToFindFourAlignTrianglesException, FoundAlignTrianglesAreNotFilledException):
                align_error += 1
                continue

            if correction_result:
                selected_indexes = correction_result.selected_indexes
                divergents = np.sum(label != np.array(selected_indexes))
                if divergents > 0:
                    # from src.debug import debug_show_image
                    # debug_show_image(correction_result.img)
                    # debug_show_image(correction_result.img_result)
                    errors += 1

    avg_error = (errors / total_amount) if total_amount > 0 else 0.0
    align_rate = (align_error / total_amount) if total_amount > 0 else 0.0
    return avg_error, align_rate, total_amount


def parallel_delegate_test(template: TemplateName, append: str, huge: bool):
    """
    This function is executed in a child process.
    It creates the TemplateData and Recognizer locally to avoid pickling issues,
    then delegates to 'delegate_test' and returns the results.
    """
    data = TemplateData()
    recognizer = Recognizer(data.new_template_matcher(template), shadow=False)
    error, align_error, total_amount = delegate_test(template, append, recognizer, huge)
    # Return a tuple that includes sorting keys plus the numeric results
    return template, append, error, align_error, total_amount


@dataclass
class TestResult:
    template: TemplateName
    append: str
    error: float
    align_error: float
    amout_of_images: int

    def as_dict(self) -> dict:
        return {
            "Template": self.template.value,
            "Append": self.append,
            "Error": self.error,
            "AlignError": self.align_error,
            "AmountOfImages": self.amout_of_images
        }

    @staticmethod
    def combine(elems: ['TestResult']) -> 'TestResult':
        assert len(elems) > 0, "A lista de TestResult está vazia."

        first_template = elems[0].template
        assert all(elem.template == first_template for elem in elems), "Todos os templates devem ser iguais para combinar."

        total_images = sum(elem.amout_of_images for elem in elems)
        assert total_images > 0, "A soma de imagens não pode ser zero."

        # Calcula a média ponderada de 'error' e 'align_error'
        weighted_error = sum(elem.error * elem.amout_of_images for elem in elems) / total_images
        weighted_align_error = sum(elem.align_error * elem.amout_of_images for elem in elems) / total_images

        return TestResult(
            template=first_template,
            append="TestResult.combine",
            error=weighted_error,
            align_error=weighted_align_error,
            amout_of_images=total_images
        )


def quality_test_parallel(huge: bool):
    """
    Parallel version of your quality_test.
    Uses ProcessPoolExecutor with max_workers=8 to speed up computations.
    """
    templates = [
        TemplateName.T_10_4, TemplateName.T_20_4, TemplateName.T_100_4,
        TemplateName.T_10_5, TemplateName.T_20_5, TemplateName.T_100_5
    ]
    appends = ["Simple", "Anullable", "Mistake", "Distort", "Complex"]

    results = []
    all_tasks = list(itertools.product(templates, appends))
    with ProcessPoolExecutor(max_workers=8) as executor, tqdm(total=len(all_tasks), desc="Executing in parallel...") as pbar:
        futures = []
        for (template, append) in all_tasks:
            future = executor.submit(parallel_delegate_test, template, append, huge)
            futures.append(future)

        for future in as_completed(futures):
            pbar.update(1)
            template, append, error, align_error, total_amount = future.result()
            results.append(TestResult(template, append, round(error, 4), round(align_error, 4), total_amount))

    results = sorted(results, key=lambda x: (templates.index(x.template), appends.index(x.append)))

    agregated = {k: [] for k in templates}
    for elem in results:
        agregated[elem.template].append(elem)

    results_json = [e.as_dict() for e in results]

    agregated_json = [
        TestResult.combine(agregated[k]).as_dict()
        for k in templates
    ]

    final_table = {
        "results": results_json,
        "agregated": agregated_json
    }

    return final_table


if __name__ == '__main__':
    output_file = relative_path("quality_test_result.json", __file__)
    table = quality_test_parallel(huge=True)

    with open(output_file, 'w') as f:
        json.dump(table, f, indent=4)

    print("Done.")
