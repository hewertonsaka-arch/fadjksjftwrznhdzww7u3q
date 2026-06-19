from PIL import Image, ImageDraw, ImageFont
import os

def create_magic_icon():
    # Cria uma imagem vazia 256x256 com fundo transparente
    img = Image.new("RGBA", (256, 256), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        # Tenta carregar a fonte de emojis do Windows
        font = ImageFont.truetype("seguiemj.ttf", 200)
    except Exception:
        # Fallback caso não encontre
        font = ImageFont.load_default()

    # Desenha o emoji da varinha mágica
    emoji = "🪄"
    
    # Para centralizar aproximadamente
    try:
        bbox = draw.textbbox((0, 0), emoji, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except:
        w, h = 200, 200
        
    x = (256 - w) / 2
    y = (256 - h) / 2
    
    # Suporte nativo a cores do Segoe UI Emoji no Pillow pode ser limitado,
    # ele as vezes desenha em preto e branco. Se não funcionar, ficará o contorno.
    draw.text((x, y - 20), emoji, font=font, fill=(0, 0, 0, 255), embedded_color=True)
    
    # Salva como .ico
    img.save("icon.ico", format="ICO", sizes=[(256, 256)])
    print("icon.ico criado com sucesso!")

if __name__ == "__main__":
    create_magic_icon()
