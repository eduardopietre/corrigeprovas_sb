import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.lines import Line2D

from src.constants import TemplateName
from src.json_handler import GridJSONHandler, KEY_BOTTOM_RIGHT, KEY_BOTTOM_LEFT, KEY_TOP_RIGHT, KEY_TOP_LEFT, KEY_TOP, \
    KEY_BOTTOM, KEY_LEFT, KEY_RIGHT


class GridConfig:
    def __init__(self, rows, cols, cell_height, margin, line_width, marker_size, options_per_cell=5, start_number=1):
        self.rows = rows
        self.cols = cols
        self.cell_height = cell_height
        self.margin = margin
        self.line_width = line_width
        self.marker_size = marker_size
        self.options_per_cell = options_per_cell
        self.start_number = start_number

    @property
    def cell_width(self):
        """Calculates cell width dynamically based on margin and options."""
        return self.margin * 2 + self.options_per_cell * self.margin


class GridDrawer:
    def __init__(self, config, figsize, json_handler, image_name):
        self.config = config
        self.figsize = figsize
        self.json_handler = json_handler
        self.image_name = image_name

    def draw_grid(self, path=None, show=False):
        """Draws the grid with all cells, lines, borders, and corner markers."""
        mpl.rcParams['figure.dpi'] = 300
        fig, ax = plt.subplots(figsize=self.figsize)
        ax.axis('off')

        self._draw_cells(ax)
        self._draw_divisions(ax)
        self._add_corner_markers(ax)
        self._add_border_references_lines(ax)
        self._adjust_plot(ax)

        dpi = fig.get_dpi()

        if path:
            fig.savefig(path, bbox_inches='tight', pad_inches=0, dpi=dpi)

        img_shape = ax.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        img_shape = np.array([img_shape.x1 - img_shape.x0, img_shape.y1 - img_shape.y0]) * dpi
        img_shape = np.floor(img_shape).astype(int).tolist()

        self.json_handler.add_image_info(self.image_name, img_shape)

        if show:
            plt.show()

    def _draw_cells(self, ax):
        """Draws all cell content (question numbers and options)."""
        cells_json = {}

        for row in range(self.config.rows):
            for col in range(self.config.cols):
                # Calculate position of each cell
                x = col * self.config.cell_width
                y = -row * self.config.cell_height
                number = self.config.start_number + row + col * self.config.rows

                text_x = x + self.config.margin
                text_y = y - (self.config.cell_height / 2) - 0.1

                # Draw question number
                ax.text(
                    text_x,
                    text_y,
                    number,
                    ha='center',
                    va='center',
                    fontsize=10,
                    weight='bold'
                )

                json_number = GridJSONHandler.number(text_x, text_y, number)
                json_checkboxes = []

                # Draw options A, B, C, D, E horizontally
                options = ['A', 'B', 'C', 'D', 'E'][:self.config.options_per_cell]
                for i, option in enumerate(options):
                    option_x = x + (3.4 - self.config.margin) + (i * 0.9)
                    option_y = y - (self.config.cell_height / 2)

                    # Option letter
                    ax.text(
                        option_x,
                        option_y + 0.45,
                        option,
                        fontsize=10,
                        va='center',
                        ha='center'
                    )

                    # Checkbox below the letter
                    checkbox_x = option_x - 0.3
                    checkbox_y = option_y - 0.6
                    checkbox_width = 0.6
                    checkbox_height = 0.6

                    checkbox = plt.Rectangle(
                        (checkbox_x, checkbox_y), checkbox_width, checkbox_height,
                        fill=None, edgecolor='black', linewidth=self.config.line_width
                    )
                    ax.add_patch(checkbox)

                    bbox = checkbox.get_bbox()
                    json_checkboxes.append(
                        GridJSONHandler.checkbox(bbox.x0, bbox.y0, bbox.x1, bbox.y1, option)
                    )

                cells_json[number] = GridJSONHandler.number_and_checkboxes(json_number, json_checkboxes)

        self.json_handler.add_cells(self.image_name, cells_json)

    def _draw_divisions(self, ax):
        """Draws the outer border and the dividing lines for rows and columns."""
        # Outer border adjusted to be closer to the cells
        border_x = 0
        border_y = -self.config.rows * self.config.cell_height
        border_width = self.config.cols * self.config.cell_width
        border_height = self.config.rows * self.config.cell_height

        ax.add_patch(plt.Rectangle(
            (border_x, border_y),
            border_width,
            border_height,
            fill=None, edgecolor='black', linewidth=self.config.line_width
        ))

        # Vertical lines (columns)
        for col in range(1, self.config.cols):
            x = col * self.config.cell_width
            ax.plot(
                [x, x],
                [-self.config.rows * self.config.cell_height, 0],
                color='black',
                linewidth=self.config.line_width
            )

        # Horizontal lines (rows)
        for row in range(1, self.config.rows):
            y = -row * self.config.cell_height
            ax.plot(
                [0, self.config.cols * self.config.cell_width],
                [y, y],
                color='black',
                linewidth=self.config.line_width
            )

    def _add_corner_mark(self, ax, x, y):
        """Draws a square corner marker."""
        marker_size = self.config.marker_size
        ax.add_patch(plt.Rectangle((x, y), marker_size, marker_size, color='black'))

    def _add_corner_triangle(self, ax, x, y, upper, color='black'):
        """Draws a triangular corner marker."""
        marker_size = self.config.marker_size
        if upper:
            cords = (
                (x, y),
                (x + marker_size, y),
                (x + (marker_size / 2), y + marker_size)
            )
        else:
            cords = (
                (x + (marker_size / 2), y),
                (x, y + marker_size),
                (x + marker_size, y + marker_size),
            )
        triangle = patches.Polygon(cords, closed=True, color=color)
        ax.add_patch(triangle)
        return cords

    def _add_corner_markers(self, ax):
        """Adds markers (triangles) to the four corners of the grid."""
        marker_size = self.config.marker_size
        marker_offset = marker_size
        height = self.config.rows * self.config.cell_height
        width = self.config.cols * self.config.cell_width

        triangles = {
            KEY_BOTTOM_LEFT: self._add_corner_triangle(ax, -marker_offset, -height - marker_offset, True),
            KEY_BOTTOM_RIGHT: self._add_corner_triangle(ax, width, -height - marker_offset, True),
            KEY_TOP_LEFT: self._add_corner_triangle(ax, -marker_offset, 0, False),
            KEY_TOP_RIGHT: self._add_corner_triangle(ax, width, 0, False),
        }

        self.json_handler.add_triangles(self.image_name, triangles)

    def _add_border_references_lines(self, ax):
        marker_size = self.config.marker_size
        padding = marker_size / 2

        spacing = marker_size * 1.5
        height = self.config.rows * self.config.cell_height
        width = self.config.cols * self.config.cell_width

        def calculate_spacing(max_value):
            start_ = 0 + spacing
            end_ = max_value - spacing
            return start_, end_

        def draw_line(p0, p1, color='black'):
            xdata = [p0[0], p1[0]]
            ydata = [p0[1], p1[1]]
            line = Line2D(xdata, ydata, color=color, linewidth=3)
            ax.add_line(line)

        # Top and bottom lines
        x0, x1 = calculate_spacing(width)

        top_p0 = [x0, padding]
        top_p1 = [x1, padding]
        draw_line(top_p0, top_p1)

        bottom_p0 = [x0, -height - padding]
        bottom_p1 = [x1, -height - padding]
        draw_line(bottom_p0, bottom_p1)

        # Left and right lines
        y0, y1 = calculate_spacing(height)

        left_p0 = [-padding, -y0]
        left_p1 = [-padding, -y1]
        draw_line(left_p0, left_p1)

        right_p0 = [width + padding, -y0]
        right_p1 = [width + padding, -y1]
        draw_line(right_p0, right_p1)

        # Save positions to json object.
        reference_lines = {
            KEY_TOP: [top_p0, top_p1],
            KEY_BOTTOM: [bottom_p0, bottom_p1],
            KEY_LEFT: [left_p0, left_p1],
            KEY_RIGHT: [right_p0, right_p1],
        }

        self.json_handler.add_reference_lines(self.image_name, reference_lines)

    def _adjust_plot(self, ax):
        """Adjusts plot limits and aspect ratio."""
        marker_size = self.config.marker_size
        ax.set_xlim(
            -marker_size,
            self.config.cols * self.config.cell_width + marker_size
        )
        ax.set_ylim(
            -self.config.rows * self.config.cell_height - marker_size,
            marker_size
        )
        ax.set_aspect('equal')


def generate():
    debug_show = False
    cell_height = 1.9
    margin = 1.0
    line_width = 1.5
    marker_size = 1.0

    json_handler = GridJSONHandler()

    to_generate = [
        (TemplateName.T_10_4.value, 5, 2, (5, 5), 4),
        (TemplateName.T_20_4.value, 10, 2, (7, 7), 4),
        (TemplateName.T_100_4.value, 20, 5, (16, 16), 4),

        (TemplateName.T_10_5.value, 5, 2, (5, 5), 5),
        (TemplateName.T_20_5.value, 10, 2, (7, 7), 5),
        (TemplateName.T_100_5.value, 20, 5, (16, 16), 5),
    ]

    for name, rows, cols, figsize, options_per_cell in to_generate:
        config = GridConfig(
            rows=rows,
            cols=cols,
            cell_height=cell_height,
            margin=margin,
            line_width=line_width,
            marker_size=marker_size,
            options_per_cell=options_per_cell
        )
        grid_drawer = GridDrawer(config, figsize, json_handler, name)
        grid_drawer.draw_grid(f"generated/{name}.png", show=debug_show)

    # Save all data to a single JSON file
    json_handler.save_to_json("generated/templates_grid_data.json")


if __name__ == '__main__':
    generate()
