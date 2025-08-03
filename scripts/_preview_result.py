import os, sys
from pathlib import Path
import cv2
import numpy as np
import threading
import time
import platform
from typing import List, Dict, Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from configs import Msg

# =========================================================================== #
# Utility Functions                                                           #
# =========================================================================== #

def insert_text(image: np.ndarray, text: str,
                font: int = cv2.FONT_HERSHEY_SIMPLEX,
                font_scale: float = 0.75,
                font_thickness: int = 1,
                text_color: tuple = (255, 255, 255),
                text_color_bg: tuple = (0, 0, 0),
                padding_x: int = 10,
                padding_y: int = 10,
                index: int = 0,
                align: str = 'left') -> None:

    h, w = image.shape[:2]
    (text_w, text_h), base = cv2.getTextSize(text, font, font_scale, font_thickness)

    stack_padding = 17
    line_spacing = text_h + stack_padding

    if align == 'right':     # ← ALIGN.RIGHT
        x = w - padding_x - text_w
    else:                    # ← ALIGN.LEFT
        x = padding_x

    y = h - padding_y - base - (index * line_spacing)

    bg_x1, bg_y1 = x, y - text_h - base
    bg_x2, bg_y2 = x + text_w, y + base

    if bg_x2 > bg_x1 and bg_y2 > bg_y1:
        roi = image[bg_y1:bg_y2, bg_x1:bg_x2]
        bg = np.full_like(roi, text_color_bg)
        blended = cv2.addWeighted(bg, 1.0, roi, 0.0, 0)
        image[bg_y1:bg_y2, bg_x1:bg_x2] = blended

    cv2.putText(image, text, (x, y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)



def resize_image(image: np.ndarray, width: Optional[int] = None, height: Optional[int] = None) -> np.ndarray:

    if width is None and height is None:
        return image

    h, w = image.shape[:2]
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))
    return cv2.resize(image, dim, interpolation=cv2.INTER_AREA)



def load_image(image_path: str) -> Optional[np.ndarray]:

    if not os.access(image_path, os.R_OK):
        return None
    try:
        img_data = np.fromfile(image_path, np.uint8)
        img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
        if img is None:
            Msg.Error(f'FAILED TO LOAD THE IMAGE FROM PATH: {image_path}')
        return img
    except Exception as e:
        Msg.Error(f'AN ERROR OCCURRED WHILE LOADING THE IMAGE: {image_path}: {e}')
        return None



# =========================================================================== #
# ImagePreviewer Class                                                        #
# =========================================================================== #

class ImagePreviewer:

    def __init__(self, data: List[Dict[str, Any]], title: str, channel: str, resize_previews: bool):

        self.data = data
        self.title = title
        self.channel = channel
        self.resize = resize_previews
        self.image_paths = []
        self.image_cache = {}
        self.paused = False
        self.current_index = 0
        self.stop_event = threading.Event()
        self.blink_thread = None
        self.play_msg = ''
        self.last_frame_time = time.time()
        self.current_fps = 30.0
        self.window_positioned = False  # WINDOWS POSITION FLAG
        self._setup_key_codes()

    def _setup_key_codes(self):

        if platform.system() == 'Darwin':  # macOS
            self.arrow_keys = {'up': 63232, 'down': 63233, 'left': 63234, 'right': 63235}
        else:  # Linux/Windows
            self.arrow_keys = {'up': (82, 0), 'down': (84, 1), 'left': (81, 2), 'right': (83, 3)}

    def _prepare_images(self) -> bool:

        downloaded_rows = [row for row in self.data if row.get('download', False)]
        if not downloaded_rows:
            Msg.Error('NO DOWNLOADED IMAGES FOUND IN THE DATA.')
            return False

        valid_paths = []

        for row in downloaded_rows:
            download_path = row.get('download_path', '')
            if not download_path or not os.path.exists(download_path):
                if download_path:
                    Msg.Warn(f'File not found, skipping: {download_path}')
                continue

            display_data = str(row.get('localtime', 'No Time Data'))
            valid_paths.append({'display_data': display_data, 'path': download_path})

        if not valid_paths:
            e = (f'NO VALID IMAGE PATHS FOUND. '
                 f'CHECK FILE PATHS AND INTEGRITY.')
            Msg.Error(e)
            return False

        self.image_paths = valid_paths
        return True



    def run(self) -> None:

        self._start_loading_indicator()
        try:
            if self._prepare_images() and self.image_paths:
                self._stop_loading_indicator()
                self.play_msg = (f'Playing preview result ({len(self.image_paths)}) images.\n'
                                 f'Press Space to pause playback, '
                                 f'Use arrow keys to navigate, '
                                 f'and Esc to exit.').upper()
                Msg.Green(self.play_msg, flush=True)
                self._preview_loop()
            else:
                self._stop_loading_indicator()
        finally:
            self._stop_loading_indicator()
            cv2.destroyAllWindows()
            if self.play_msg:
                self._clear_msg(self.play_msg)



    def _preview_loop(self) -> None:

        RESIZE_VALUE = 0.5    # ← RESIZE.IMAGE.PREVIEW

        while True:

            self.frame_start_time = time.time()

            if not self.paused:
                self.current_index = (self.current_index + 1) % len(self.image_paths)

            info = self.image_paths[self.current_index]


            img = self._get_cached_image(info['path'])
            if img is None:
                continue

            img_display = img.copy()
            h, w = img_display.shape[:2]

            # *** WINDOW.TITLE *** #
            title = f'{self.title.upper()} ({w}px, {h}px)'
            try:
                win_title = title.encode('utf-8').decode(sys.getfilesystemencoding())
            except (UnicodeEncodeError, UnicodeDecodeError):
                win_title = title
            # *** WINDOW.TITLE *** #

            # *** RESIZE *** #
            if self.resize:
                img_display = resize_image(img_display, width=int(w * RESIZE_VALUE))
            # *** RESIZE *** #

            # *** FPS / STAND-BY *** #
            if not self.paused:
                current_time = time.time()
                if hasattr(self, 'last_frame_time'):
                    frame_time = current_time - self.last_frame_time
                    if frame_time > 0:
                        self.current_fps = 1.0 / frame_time
                self.last_frame_time = current_time

                target_frame_time = 1.0 / 30.0  # 33.33ms
                processing_time = current_time - (getattr(self, 'frame_start_time', current_time))
                wait_time = max(1, int((target_frame_time - processing_time) * 1000))
            else:
                wait_time = 0
            # *** FPS / STAND-BY *** #

            # *** INSERT.TEXT *** #
            insert_text(img_display, f'{self.current_index:04d}/{len(self.image_paths) - 1:04d}', index=1)
            insert_text(img_display, f'{info["display_data"]}', index=0)
            insert_text(img_display, f'{self.current_fps:.1f} FPS', index=0, align='right')
            # *** INSERT.TEXT *** #

            cv2.imshow(win_title, img_display)

            # *** WINDOW.POSITION *** #
            if not self.window_positioned:
                cv2.moveWindow(win_title, 700, 300)    # ← SET WINDOW POSITION
                self.window_positioned = True
            # *** WINDOW.POSITION *** #

            key = cv2.waitKey(wait_time) & 0xFF

            if self._handle_input(key) or cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) <= 0:
                break


    def _handle_input(self, key: int) -> bool:

        if key == 27: # ESC: Exit Preview
            return True
        elif key == 32: # Space: Pause/Play Toggle
            self.paused = not self.paused
        elif key in (self.arrow_keys['up'] if isinstance(self.arrow_keys['up'], tuple) else (self.arrow_keys['up'],)):
            # Up Arrow: Go to First Image
            self.paused, self.current_index = True, 0
        elif key in (self.arrow_keys['down'] if isinstance(self.arrow_keys['down'], tuple) else (self.arrow_keys['down'],)):
            # Down Arrow: Go to Last Image
            self.paused, self.current_index = True, len(self.image_paths) - 1
        elif key in (self.arrow_keys['left'] if isinstance(self.arrow_keys['left'], tuple) else (self.arrow_keys['left'],)):
            # Left Arrow: Go to Previous Image
            self.paused, self.current_index = True, (self.current_index - 1 + len(self.image_paths)) % len(self.image_paths)
        elif key in (self.arrow_keys['right'] if isinstance(self.arrow_keys['right'], tuple) else (self.arrow_keys['right'],)):
            # Right Arrow: Go to Next Image
            self.paused, self.current_index = True, (self.current_index + 1) % len(self.image_paths)
        return False




    def _start_loading_indicator(self) -> None:

        if self.blink_thread is None or not self.blink_thread.is_alive():
            self.stop_event.clear()
            self.blink_thread = threading.Thread(
                target=Msg.Blink,
                args=('LOADING RESULT PREVIEW. PLEASE WAIT⋯',),
                kwargs={'stop_event': self.stop_event,
                        'clear_on_finish': True,
                        'color': 'White'}
            )
            self.blink_thread.daemon = True
            self.blink_thread.start()
            # time.sleep(0.05)  # ← 핵심 추가: Blink 출력 여유 시간 확보



    def _stop_loading_indicator(self) -> None:

        if self.blink_thread is not None and self.blink_thread.is_alive():
            self.stop_event.set()
            self.blink_thread.join(timeout=0.2)



    def _get_cached_image(self, image_path: str) -> Optional[np.ndarray]:

        if image_path in self.image_cache:
            return self.image_cache[image_path]

        img = load_image(image_path)

        if img is not None:

            if len(self.image_cache) >= 5:
                oldest_key = next(iter(self.image_cache))
                del self.image_cache[oldest_key]

            self.image_cache[image_path] = img

        return img

    def _clear_msg(self, message: str):

        num_lines = message.count('\n')

        for _ in range(num_lines):
            sys.stdout.write('\033[A\033[K')
        sys.stdout.write('\r')
        sys.stdout.flush()

# =========================================================================== #
# Main Function
# =========================================================================== #

def preview_result(data: List[Dict[str, Any]], success_count: int, resize: bool = True) -> None:

    if success_count <= 0:
        Msg.Error(f'NO VALID AND LOADABLE IMAGES FOUND.')
        return False

    first_row = data[0] if data else {}

    title = (f'{first_row.get("satellite", "")}_'
             f'{first_row.get("sensor", "")}_'
             f'{first_row.get("level", "")}_'
             f'{first_row.get("area", "")}_'
             f'{first_row.get("channel", "")}')

    channel =(f'{first_row.get("area", "")}_'
              f'{first_row.get("channel", "")}')

    previewer = ImagePreviewer(data, title, channel, resize)
    previewer.run()


def main() -> None:
    return None

if __name__ == '__main__':
    main()