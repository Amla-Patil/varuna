import cv2
from pathlib import Path


def draw_detections(
    image_path: str,
    results: dict,
    output_path: str,
) -> None:
    """
    Draw YOLO detections on the original sonar image.

    Parameters
    ----------
    image_path : str
        Path to the original sonar image.

    results : dict
        Detection results returned by SonarInferencePipeline.

    output_path : str
        Path where the annotated image will be saved.
    """

    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    for detection in results.get("detections", []):
        bbox = detection["bbox"]

        x1 = int(round(bbox["x1"]))
        y1 = int(round(bbox["y1"]))
        x2 = int(round(bbox["x2"]))
        y2 = int(round(bbox["y2"]))

        class_name = detection["class_name"]
        confidence = detection["confidence_percent"]

        label = f"{class_name} {confidence:.1f}%"

        # Draw bounding box.
        cv2.rectangle(
            image,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2,
        )

        # Calculate label size.
        (text_width, text_height), baseline = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            2,
        )

        label_y1 = max(0, y1 - text_height - baseline - 6)
        label_y2 = y1

        # Label background.
        cv2.rectangle(
            image,
            (x1, label_y1),
            (x1 + text_width + 6, label_y2),
            (0, 255, 0),
            -1,
        )

        # Label text.
        cv2.putText(
            image,
            label,
            (x1 + 3, y1 - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 0),
            2,
            cv2.LINE_AA,
        )

    # Add summary in the top-left corner.
    count = results.get("detection_count", 0)

    summary = f"Detections: {count}"

    cv2.putText(
        image,
        summary,
        (15, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    success = cv2.imwrite(
        str(output_path),
        image,
    )

    if not success:
        raise IOError(
            f"Could not save overlay: {output_path}"
        )