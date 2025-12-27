import cv2

from src.json_handler import GridJSONHandler
from src.debug import debug_show_image


def draw_red_dots(image, data):
    radius = 9
    for key, cell in data["cells"].items():
        n = cell["number"]
        cv2.circle(image, (n["x"], n["y"]), radius, (255, 0, 255), -1)  # Círculo rosa

        for e in cell["checkboxes"]:
            cv2.circle(image, (e["x0"], e["y0"]), radius, (0, 0, 255), -1)  # Círculo vermelho
            cv2.circle(image, (e["x1"], e["y1"]), radius, (0, 255, 0), -1)  # Círculo verde

    # Exibe a imagem resultante
    debug_show_image(image)


if __name__ == "__main__":
    json_data = GridJSONHandler.load_from_json("generated/templates_grid_data.json")
    for k, v in json_data.data.items():
        image = cv2.imread(f"generated/{k}.png")
        draw_red_dots(image, v)
