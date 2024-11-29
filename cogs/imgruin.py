import discord
import random
from discord.ext import commands
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import io
import aiohttp
import asyncio

class ImageMutilationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        asyncio.create_task(self.session.close())

    async def get_image_url(self, ctx, url=None):
        # If a URL is provided directly
        if url:
            return url

        # Check for attachments in the invoking message
        if ctx.message.attachments:
            return ctx.message.attachments[0].url

        # Check if the message is a reply
        if ctx.message.reference:
            replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            # Check for attachments or embed images in the replied message
            if replied_msg.attachments:
                return replied_msg.attachments[0].url
            elif replied_msg.embeds and replied_msg.embeds[0].image:
                return replied_msg.embeds[0].image.url

        # Check for mentioned users (use their avatar)
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
            return user.display_avatar.url

        # No image found
        return None

    async def process_image(self, ctx, effect_func, *args, **kwargs):
        # Get the image URL
        image_url = await self.get_image_url(ctx)
        if not image_url:
            await ctx.send("No image found. Please provide an image.")
            return

        # Download the image
        async with self.session.get(str(image_url)) as resp:
            if resp.status != 200:
                await ctx.send("Failed to download the image.")
                return
            image_data = await resp.read()

        # Open and process the image
        with Image.open(io.BytesIO(image_data)) as image:
            result = effect_func(image, *args, **kwargs)

            # If the result is a buffer (e.g., for GIFs), send it directly
            if isinstance(result, io.BytesIO):
                buffer = result
            else:
                # Save the processed image to a BytesIO buffer
                buffer = io.BytesIO()
                result.save(buffer, format="PNG")
                buffer.seek(0)

        # Send the image to Discord
        await ctx.send(file=discord.File(buffer, "processed_image.png"))

    @commands.command()
    async def pixelate(self, ctx):
        """Pixelate the image."""
        def effect(image):
            small = image.resize((16, 16), resample=Image.BILINEAR)
            return small.resize(image.size, Image.NEAREST)
        await self.process_image(ctx, effect)

    @commands.command()
    async def distort(self, ctx):
        """Apply random distortions to the image."""
        def effect(image):
            return image.transform(
                image.size,
                Image.AFFINE,
                (1, 0.2, 0, 0.2, 1, 0)
            )
        await self.process_image(ctx, effect)

    @commands.command()
    async def rain(self, ctx):
        """Add a rain effect to the image."""
        def effect(image):
            overlay = Image.new("RGBA", image.size, (255, 255, 255, 50))
            image = image.convert("RGBA")
            return Image.alpha_composite(image, overlay).filter(ImageFilter.GaussianBlur(5))
        await self.process_image(ctx, effect)

    @commands.command()
    async def spin(self, ctx):
        """Create a spinning animation of the image."""
        def effect(image):
            frames = []
            for angle in range(0, 360, 30):
                rotated_image = image.rotate(angle, expand=True).convert('RGB')
                frames.append(rotated_image)

            # Save frames to a BytesIO buffer as a GIF
            gif_buffer = io.BytesIO()
            frames[0].save(
                gif_buffer,
                format='GIF',
                save_all=True,
                append_images=frames[1:],
                loop=0,
                duration=100,
                disposal=2
            )
            gif_buffer.seek(0)
            return gif_buffer

        # Get the image URL
        image_url = await self.get_image_url(ctx)
        if not image_url:
            await ctx.send("No image found. Please provide an image.")
            return

        # Download the image
        async with self.session.get(str(image_url)) as resp:
            if resp.status != 200:
                await ctx.send("Failed to download the image.")
                return
            image_data = await resp.read()

        # Open and process the image
        with Image.open(io.BytesIO(image_data)) as image:
            buffer = effect(image)

        # Send the GIF to Discord
        await ctx.send(file=discord.File(buffer, "spin.gif"))

    @commands.command()
    async def invert(self, ctx):
        """Invert the colors of the image."""
        def effect(image):
            return ImageOps.invert(image.convert("RGB"))
        await self.process_image(ctx, effect)

    @commands.command()
    async def grayscale(self, ctx):
        """Convert the image to grayscale."""
        def effect(image):
            return ImageOps.grayscale(image)
        await self.process_image(ctx, effect)

    @commands.command()
    async def blur(self, ctx, radius: float = 2.0):
        """Blur the image."""
        def effect(image):
            return image.filter(ImageFilter.GaussianBlur(radius=radius))
        await self.process_image(ctx, effect)

    @commands.command()
    async def warp(self, ctx):
        """Warp the image with a rotation effect."""
        async def effect(image):
            return image.transpose(Image.ROTATE_90)
        await self.process_image(ctx, effect)
        
    @commands.command()
    async def deepfry(self, ctx):
        """Deep-fry the image."""
        def effect(image):
            image = image.convert("RGB")
            image = ImageEnhance.Contrast(image).enhance(2)
            image = ImageEnhance.Sharpness(image).enhance(5)
            image = ImageEnhance.Color(image).enhance(2)
            return image.filter(ImageFilter.EDGE_ENHANCE_MORE)
        await self.process_image(ctx, effect)

    @commands.command()
    async def colorize(self, ctx, color_hex: str):
        """Change the image color based on a hex code."""
        # Validate the hex code
        if len(color_hex) not in [3, 6]:
            await ctx.send("Please provide a valid hex color code (3 or 6 digits).")
            return

        # Expand 3-digit hex codes to 6-digit
        if len(color_hex) == 3:
            color_hex = ''.join([c*2 for c in color_hex])

        try:
            r, g, b = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            await ctx.send("Please provide a valid hex color code.")
            return

        def effect(image):
            color_image = Image.new("RGB", image.size, (r, g, b))
            return Image.blend(image.convert("RGB"), color_image, 0.5)
        await self.process_image(ctx, effect)

    @commands.command()
    async def sharpen(self, ctx):
        """Sharpen the image."""
        def effect(image):
            return image.filter(ImageFilter.SHARPEN)
        await self.process_image(ctx, effect)

    @commands.command()
    async def emboss(self, ctx):
        """Apply emboss effect to the image."""
        def effect(image):
            return image.filter(ImageFilter.EMBOSS)
        await self.process_image(ctx, effect)

    @commands.command()
    async def edge(self, ctx):
        """Detect edges in the image."""
        def effect(image):
            return image.filter(ImageFilter.FIND_EDGES)
        await self.process_image(ctx, effect)

    @commands.command()
    async def flip(self, ctx):
        """Flip the image vertically."""
        def effect(image):
            return ImageOps.flip(image)
        await self.process_image(ctx, effect)

    @commands.command()
    async def magic(self, ctx):
        """Apply a cursed effect to the image."""
        def effect(image):
            image = image.convert("RGB")
            # Random color shift
            r, g, b = image.split()
            r = r.point(lambda i: min(255, int(i * 0.9)))
            g = g.point(lambda i: min(255, int(i * 1.1)))
            b = b.point(lambda i: min(255, int(i * 0.9)))
            image = Image.merge('RGB', (r, g, b))

            # Over-sharpen
            image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

            # Add noise
            import random
            pixels = image.load()
            width, height = image.size
            for x in range(width):
                for y in range(height):
                    rand = random.randint(-30, 30)
                    r, g, b = pixels[x, y]
                    r = max(0, min(255, r + rand))
                    g = max(0, min(255, g + rand))
                    b = max(0, min(255, b + rand))
                    pixels[x, y] = (r, g, b)

            # Slightly distort the image
            #image = image.transform(
            #    image.size,
            #    Image.AFFINE,
            #    (1, 0.1, 0, 0.1, 1, 0),
            #    resample=Image.BICUBIC
            #)

            return image

        await self.process_image(ctx, effect)

async def setup(bot):
    await bot.add_cog(ImageMutilationCog(bot))