"""Image Extraction Service Module
Handles image extraction operations from PDF documents.

This module provides:
- Image extraction interface for PDF files
"""

import logging
import fitz
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_images_from_pdf(pdf_path: str, output_dir: str) -> List[Dict[str, Any]]:
    """
    Extract images from a PDF document.

    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted images

    Returns:
        List of dictionaries containing image information:
        - path: Path to the extracted image file
        - page: Page number (0-indexed)
        - image_index: Index of the image on the page

    Returns an empty list if no images are found.
    """
    logger.info(f"Extracting images from PDF: {pdf_path}")
    logger.info(f"Output directory: {output_dir}")

    # TODO: Implement PDF image extraction and return list[dict].
    #
    # HINT:
    # - Open the PDF and iterate through its pages
    # - Detect and extract embedded images
    # - Save each extracted image into `output_dir`
    # - Return a list of dicts with keys: "path", "page", "image_index"
    #
    # Your code here:
    logger.info("Extracting images from PDF: %s", pdf_path)
    logger.info("Output directory: %s", output_dir)

    extracted_images: List[Dict[str, Any]] = []
    pdf_file = Path(pdf_path)
    output_path = Path(output_dir)

    if not pdf_file.exists():
        logger.error(f"PDF file not found at path {pdf_path}")
        return []

    output_path.mkdir(parents=True, exist_ok=True)
    doc = None

    try:
        doc = fitz.open(pdf_path)
        for page_index in range(len(doc)):
            page = doc[page_index]
            image_list = page.get_images(full=True)

            logger.info("Found %d images on page %d", len(image_list), page_index)

            for image_index, image in enumerate(image_list):
                xref = image[0]

                try:
                    base_image = doc.extract_image(xref)

                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    image_filename = (
                        f"page_{page_index}_image_{image_index}.{image_ext}"
                    )

                    image_filepath = output_path / image_filename

                    with open(image_filepath, "wb", encoding="utf-8") as image_file:
                        image_file.write(image_bytes)

                    image_info = {
                        "path": str(image_filepath),
                        "page": page_index,
                        "image_index": image_index,
                    }

                    extracted_images.append(image_info)

                    logger.info(
                        "Extracted image saved: %s",
                        image_filepath,
                    )

                except Exception as image_error:
                    logger.error(
                        "Failed to extract image %d from page %d: %s",
                        image_index,
                        page_index,
                        image_error,
                    )

    except Exception as pdf_error:
        logger.error("Failed to process PDF %s: %s", pdf_path, pdf_error)

    finally:
        if doc is not None:
            doc.close()

    logger.info(
        "Completed image extraction total images extracted: %d", len(extracted_images)
    )

    return extracted_images
