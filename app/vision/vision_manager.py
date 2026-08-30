"""Vision module - Image analysis and multimodal input.

Provides image understanding capabilities for the Input Layer.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class VisionManager:
    """Manages image/video analysis for multimodal input.

    Supports:
      - Image file analysis
      - Screenshot capture
      - Camera input
      - OCR extraction
      - Multimodal LLM integration
    """

    def __init__(self, llm_router=None):
        self.llm_router = llm_router
        self._camera_available = False
        self._ocr_available = False

    def initialize(self):
        """Try to initialize vision capabilities."""
        try:
            import cv2
            self._camera_available = True
        except ImportError:
            pass

        try:
            import pytesseract
            self._ocr_available = True
        except ImportError:
            pass

    def analyze(self, image_source: Any) -> Dict[str, Any]:
        """Analyze an image and return description + metadata.

        Args:
            image_source: File path, numpy array, or PIL Image.

        Returns:
            Dict with description, confidence, and metadata.
        """
        result = {
            "description": "",
            "confidence": 0.0,
            "metadata": {},
            "source": "image"
        }

        if self.llm_router and self._has_multimodal_support():
            description = self._analyze_with_multimodal_llm(image_source)
            if description:
                result["description"] = description
                result["confidence"] = 0.85
                return result

        if self._ocr_available:
            text = self._extract_text_ocr(image_source)
            if text:
                result["description"] = f"Image contains text: {text[:500]}"
                result["confidence"] = 0.7
                result["metadata"]["ocr_text"] = text
                return result

        result["description"] = "[Image received - analysis pending multimodal LLM]"
        result["confidence"] = 0.3
        return result

    def capture_screenshot(self) -> Optional[Any]:
        """Capture current screen."""
        if not self._camera_available:
            return None
        try:
            import cv2
            import numpy as np
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception:
            return None

    def capture_camera(self) -> Optional[Any]:
        """Capture from webcam."""
        if not self._camera_available:
            return None
        try:
            import cv2
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            return frame if ret else None
        except Exception:
            return None

    def _has_multimodal_support(self) -> bool:
        """Check if current LLM provider supports vision."""
        if not self.llm_router:
            return False
        for provider in self.llm_router.providers.values():
            if hasattr(provider, "supports_vision") and provider.supports_vision:
                return True
            if hasattr(provider, "complete_vision"):
                return True
        return False

    def _analyze_with_multimodal_llm(self, image_source: Any) -> Optional[str]:
        """Use multimodal LLM to analyze image."""
        try:
            for provider in self.llm_router.providers.values():
                if hasattr(provider, "complete_vision"):
                    return provider.complete_vision(image_source, prompt="Describe this image in detail.")
        except Exception:
            pass
        return None

    def _extract_text_ocr(self, image_source: Any) -> str:
        """Extract text from image using OCR."""
        try:
            import pytesseract
            from PIL import Image
            if hasattr(image_source, "convert"):
                return pytesseract.image_to_string(image_source)
            return ""
        except Exception:
            return ""
