import calendar
import io
from datetime import date, datetime, timedelta, timezone

from PIL import Image, ImageDraw, ImageFont


def compute_streaks(
        activity_dates: list[date],
        reference_date: date | None = None,
) -> tuple[int, int, date | None, date | None, date | None]:
    """
    Returns (current_streak, longest_streak, longest_start, longest_end, expiry_date).
    expiry_date is the UTC date (starting at 00:00:00) after which the streak is lost.
    activity_dates must be sorted descending with distinct calendar days.
    """
    today = reference_date or datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)

    if not activity_dates:
        return 0, 0, None, None, None

    most_recent = activity_dates[0]
    is_active = most_recent >= yesterday

    current_streak = 1 if is_active else 0
    longest_streak = 1
    longest_start = activity_dates[0]
    longest_end = activity_dates[0]

    temp_streak = 1
    temp_start = activity_dates[0]

    # Single pass calculation for both current and longest streaks
    for i in range(1, len(activity_dates)):
        if activity_dates[i] == activity_dates[i - 1] - timedelta(days=1):
            temp_streak += 1
            # If we are still in the first consecutive run from the most recent activity
            if is_active and current_streak == i:
                current_streak += 1
        else:
            if temp_streak >= longest_streak:
                longest_streak = temp_streak
                # activity_dates is DESC, so temp_start is the latest day,
                # activity_dates[i-1] is the earliest day of the run
                longest_start = activity_dates[i - 1]
                longest_end = temp_start

            temp_streak = 1
            temp_start = activity_dates[i]

    if temp_streak >= longest_streak:
        longest_streak = temp_streak
        longest_start = activity_dates[-1]
        longest_end = temp_start

    expiry_date = most_recent + timedelta(days=2) if is_active else None

    return current_streak, longest_streak, longest_start, longest_end, expiry_date


def _draw_striped_rect(
        image: Image.Image,
        x: int,
        y: int,
        size: int,
        color1: tuple,
        color2: tuple,
        radius: int,
        padding: int = 4
):
    """
    Internal helper to draw a rounded rectangle with alternating diagonal stripes.
    Requested: -45° orientation, 5px each band.
    """
    draw = ImageDraw.Draw(image)
    box = [x + padding, y + padding, x + size - padding, y + size - padding]

    # Draw background color1 (Sand)
    draw.rounded_rectangle(box, radius=radius, fill=color1)

    # Create mask for stripes
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    # Respect rounded corners on mask
    mask_draw.rounded_rectangle([padding, padding, size - padding, size - padding], radius=radius, fill=255)

    # Draw diagonal stripes onto a layer
    stripe_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(stripe_layer)

    band_width = 5
    frequency = band_width * 2

    for offset in range(0, size * 2, frequency):
        # Sky blue band
        points = [
            (offset, 0),
            (offset + band_width, 0),
            (offset + band_width - size, size),
            (offset - size, size)
        ]
        layer_draw.polygon(points, fill=color2)

    # Paste stripes using the rounded mask
    image.paste(stripe_layer, (x, y), mask)


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Robust font loader with multi-platform fallbacks."""
    font_names = [
        "arial.ttf",  # Windows
        "DejaVuSans.ttf",  # Linux
        "Ubuntu-R.ttf",  # Linux
        "Helvetica.ttc",  # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def generate_streak_calendar_image(
        voyage_dates: list[date],
        hosted_dates: list[date],
        year: int,
        month: int,
) -> bytes:
    """
    Generates a PNG image of a calendar for the specified month.
    Highlights days with activity using requested Sand (#BA7517) & Sky (#378ADD) palette.
    Logic: 
    - Solid Sky (#378ADD) = Voyaged
    - Striped (Sand+Sky) = Hosted (which implies voyaged)
    """
    # UI Constants
    CELL_SIZE = 60
    RADIUS = 12
    PADDING = 40
    HEADER_HEIGHT = 80
    DAY_NAMES_HEIGHT = 40
    LEGEND_HEIGHT = 60

    WIDTH = (CELL_SIZE * 7) + (2 * PADDING)
    HEIGHT = HEADER_HEIGHT + DAY_NAMES_HEIGHT + (CELL_SIZE * 6) + PADDING + LEGEND_HEIGHT

    # User Requested Palette
    BG_COLOR = (24, 25, 28)  # Deep carbon gray
    EMPTY_COLOR = (43, 45, 49)  # Subtle, quiet cell background

    SAND_COLOR = (186, 117, 23)  # Sand (#BA7517)
    SKY_COLOR = (55, 138, 221)  # Sky (#378ADD)

    # Text colors
    LIGHT_TEXT = (235, 237, 239)  # Off-white
    MUTED_TEXT = (148, 155, 164)
    TODAY_COLOR = (255, 255, 255)  # White highlight

    image = Image.new("RGBA", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(image)

    title_font = _get_font(32)
    day_font = _get_font(20)
    number_font = _get_font(24)
    legend_font = _get_font(18)

    # Draw Header
    month_name = calendar.month_name[month]
    header_text = f"{month_name} {year}"
    draw.text((WIDTH // 2, PADDING + 20), header_text, fill=LIGHT_TEXT, font=title_font, anchor="mm")

    # Draw Day Names
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for i, day in enumerate(days):
        x = PADDING + (i * CELL_SIZE) + (CELL_SIZE // 2)
        y = HEADER_HEIGHT + PADDING
        draw.text((x, y), day, fill=MUTED_TEXT, font=day_font, anchor="mm")

    # Draw Days
    cal = calendar.Calendar(firstweekday=6)  # 6 = Sunday
    month_days = cal.monthdayscalendar(year, month)

    voyage_set = set(voyage_dates)
    hosted_set = set(hosted_dates)
    today = datetime.now(timezone.utc).date()

    for row_idx, week in enumerate(month_days):
        for col_idx, day_num in enumerate(week):
            if day_num == 0:
                continue

            x_start = PADDING + (col_idx * CELL_SIZE)
            y_start = HEADER_HEIGHT + DAY_NAMES_HEIGHT + PADDING + (row_idx * CELL_SIZE)

            x_center = x_start + (CELL_SIZE // 2)
            y_center = y_start + (CELL_SIZE // 2)

            current_date = date(year, month, day_num)
            has_voyage = current_date in voyage_set
            has_hosted = current_date in hosted_set

            # 1. Draw base quiet cell
            cell_box = [x_start + 4, y_start + 4, x_start + CELL_SIZE - 4, y_start + CELL_SIZE - 4]
            draw.rounded_rectangle(cell_box, radius=RADIUS, fill=EMPTY_COLOR)

            # 2. Draw activity content
            if has_hosted:
                _draw_striped_rect(image, x_start, y_start, CELL_SIZE, SAND_COLOR, SKY_COLOR, RADIUS)
            elif has_voyage:
                draw.rounded_rectangle(cell_box, radius=RADIUS, fill=SKY_COLOR)

            # 3. Day Number
            draw.text((x_center, y_center), str(day_num), fill=LIGHT_TEXT, font=number_font, anchor="mm")

            # 4. Border if today
            if current_date == today:
                draw.rounded_rectangle(cell_box, radius=RADIUS, outline=TODAY_COLOR, width=3)

    # Draw Legend
    legend_y = HEIGHT - (LEGEND_HEIGHT // 2) - 10
    legend_items = [
        (SKY_COLOR, "Voyaged"),
        (None, "Hosted")
    ]

    total_legend_width = sum(len(text) * 10 + 60 for _, text in legend_items)
    current_x = (WIDTH - total_legend_width) // 2

    for color, label in legend_items:
        if label == "Hosted":
            _draw_striped_rect(image, current_x - 20, legend_y - 30, 60, SAND_COLOR, SKY_COLOR, 4, padding=20)
            text_x = current_x + 28
        else:
            box_coords = [current_x, legend_y - 10, current_x + 20, legend_y + 10]
            draw.rounded_rectangle(box_coords, radius=4, fill=color)
            text_x = current_x + 28

        draw.text((text_x, legend_y), label, fill=LIGHT_TEXT, font=legend_font, anchor="lm")
        current_x += len(label) * 10 + 60

    # Save to buffer
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()
