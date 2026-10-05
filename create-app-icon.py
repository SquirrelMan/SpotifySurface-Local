"""產生不含地理圖案的音符圖示，供視窗與 EXE 共用。"""
from pathlib import Path
from PIL import Image, ImageDraw


def createIcon() -> None:
    """使用幾何音符避免字型差異影響圖示外觀。"""
    image = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((8, 8, 248, 248), radius=52, fill="#161616")
    draw.polygon([(112, 63), (195, 43), (195, 166), (176, 166), (176, 86), (132, 97), (132, 186), (112, 186)], fill="#1ed760")
    draw.ellipse((67, 163, 132, 208), fill="#1ed760")
    draw.ellipse((131, 144, 195, 189), fill="#1ed760")
    target = Path(__file__).parent / "assets" / "app-icon.ico"
    image.save(target, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


if __name__ == "__main__":
    createIcon()
