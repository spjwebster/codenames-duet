import random
import os.path
import json
from typing import Any
from dataclasses import replace
from enum import Enum
from math import floor, ceil

from PIL import Image, ImageDraw, ImageFont
import click

from core import *
from util import mm_to_px, chunk, Point, centred_pos

OUTPUT_DPI = 300
A4_WIDTH_MM = 210
A4_HEIGHT_MM = 297
A4_MARGINS_MM = 25

class TextAlign(Enum):
    LEFT = 'left'
    MIDDLE = 'middle'
    RIGHT = 'right'

class AssetPack:
    name:str
    
    config:dict[str, Any]

    bg_img:Image
    tile_images:dict
    font:ImageFont

    font_file:str
    font_size:int
    
    text_offset:Point
    text_align:str
    text_colour:str

    tile_offset:Point
    tile_spacing:Point

    def __init__(self, name:str, config:dict) -> None:
        self.name = name
        
        self.font_file = config['font-file']
        self.font_size = config['font-size']
        self.text_offset = Point.from_dict(config['text-offset'])
        self.text_colour = config['text-colour']
        self.text_align = TextAlign(config['text-align'] if 'text-align' in config else 'left')
        self.tile_offset = Point.from_dict(config['tile-offset'])
        self.tile_spacing = Point.from_dict(config['tile-spacing'])

        self.load_all()

    @property
    def path(self) -> str:
        return f"assets/{self.name}"
    
    def load_all(self):
        self.bg_img = Image.open(f"{self.path}/card-background.png")
        self.tile_images = {
            TileType.BYSTANDER: Image.open(f"{self.path}/tile-neutral.png"),
            TileType.ASSASSIN: Image.open(f"{self.path}/tile-assassin.png"),
            TileType.AGENT: Image.open(f"{self.path}/tile-agent.png"),
        }
        self.font = ImageFont.truetype(
            f"{self.path}/{self.font_file}", 
            self.font_size
        )

def create_card_image(assets:AssetPack, grid:list[str], seed:int, side:str) -> Image:
    output_image = Image.new("RGBA", assets.bg_img.size)
    output_image.paste(assets.bg_img, (0,0), assets.bg_img)

    (tile_width, tile_height) = assets.tile_images[TileType.BYSTANDER].size

    for row_index, row in enumerate(chunk(grid, 5)):
        offset_y = assets.tile_offset.y + row_index * (tile_height + assets.tile_spacing.y)

        for col_index, tile_type in enumerate(row):
            offset_x = assets.tile_offset.x + col_index * (tile_width + assets.tile_spacing.x)

            img = assets.tile_images[tile_type]
            output_image.paste(img, (offset_x, offset_y), img)

    # Draw card number/side text
    d = ImageDraw.Draw(output_image)
    text = f"{seed:04d}/{side}"

    # Calculate text position based on alignment
    text_pos = replace(assets.text_offset)
    if (assets.text_align != TextAlign.LEFT):
        _, _, text_width, text_height = d.textbbox((0, 0), text, font=assets.font)        
        
        if (assets.text_align == TextAlign.MIDDLE):
            text_pos.x -= text_width / 2
        elif (assets.text_align == TextAlign.MIDDLE):
            text_pos.x -= text_width
    
    d.text((text_pos.x, text_pos.y), f"{seed:04d}/{side}", font=assets.font, fill=assets.text_colour)

    return output_image

def save_card_image(image:Image.Image, filename:str):
    # Save image
    dir = os.path.dirname(filename)
    if not os.path.exists(dir):
        os.makedirs(dir)
    
    image.save(filename)

def load_asset_packs(names:list[str]) -> list[AssetPack]:
    return [
        load_asset_pack(name)
        for name in names
    ]

def load_asset_pack(name:str) -> AssetPack:
    asset_path = f'assets/{name}'
    with open(f'{asset_path}/config.json') as f:
        config = json.loads(f.read())

    asset_pack = AssetPack(name, config)

    return asset_pack

@click.group()
def cli():
    pass

@cli.command()
@click.option('--count', '-c', default=100, help='Number of cards to generate.')
@click.option('--seed', '-s', default=1, help='Starting seed.')
def text(count, seed):
    for i in range(0, count):
        random.seed(seed + i)
        (a, b) = generate_word_grids()        
        check_grids(a, b)

        b = reverse_grid(b)        

        print('a')
        for row in chunk(a, 5):
            print([t.value for t in row])

        print('b')
        for row in chunk(b, 5):
            print([t.value for t in row])

        print('---')

@cli.command()
@click.argument('template', nargs=-1, required=True)
@click.option('--count', '-c', default=100, help='Number of cards to generate.')
@click.option('--seed', '-s', default=1, help='Starting seed.')
@click.option('--output-dir', '-o', default='output/', help='Output base directory.')
def images(count, seed, template, output_dir):
    asset_packs = load_asset_packs(template)

    for i in range(0, count):
        current_seed = seed + i
        random.seed(current_seed)

        (a, b) = generate_word_grids()
        check_grids(a, b)

        for asset_pack in asset_packs:
            print(f"Writing {asset_pack.name} {current_seed:04d}")
            template_output_dir = os.path.join(output_dir, asset_pack.name)

            image = create_card_image(asset_pack, a, current_seed, 'A')
            save_card_image(image, f'{template_output_dir}/{current_seed}-a.png')

            b = reverse_grid(b)
            image = create_card_image(asset_pack, b, current_seed, 'B')
            save_card_image(image, f'{template_output_dir}/{current_seed}-b.png')

@cli.command()
@click.argument('template', nargs=-1, required=True)
@click.option('--count', '-c', default=100, help='Number of cards to generate.')
@click.option('--seed', '-s', default=1, help='Starting seed.')
@click.option('--output-dir', '-o', default='output', help='Output base directory.')
@click.option('--dpi', '-d', default=OUTPUT_DPI, type=int, help='Output DPI.')
def pdf(count, seed, template, output_dir, dpi):
    asset_packs = load_asset_packs(template)

    # TODO: Make configurable and support crop margins
    images_per_page = 8
    images_per_row = 2
    image_spacing = Point(mm_to_px(10, dpi), mm_to_px(10, dpi))
    page_dimensions = (mm_to_px(A4_WIDTH_MM, dpi), mm_to_px(A4_HEIGHT_MM, dpi))
    page_middle_x = round(page_dimensions[0] / 2)
    target_image_width = mm_to_px(68, dpi)

    for asset_pack in asset_packs:
        pages: list[Image.Image] = []
        page_a = None
        page_b = None

        output_filename = os.path.join(output_dir, f'{asset_pack.name}.pdf')

        with click.progressbar(range(0, count), length=count, label=f"Generating {output_filename}") as images:

            for i in images:
                current_seed = seed + i
                random.seed(current_seed)

                (a, b) = generate_word_grids()
                check_grids(a, b)

                b = reverse_grid(b)

                page_index = i % images_per_page
                if page_index == 0:
                    # Create new pages
                    page_a = Image.new("RGBA", page_dimensions, '#ffffff')
                    pages.append(page_a)
                    page_b = Image.new("RGBA", page_dimensions, '#ffffff')
                    pages.append(page_b)

                # TODO: Refactor to DRY between images A and B

                # Create images
                image_a = create_card_image(asset_pack, a, current_seed, 'A')
                image_b = create_card_image(asset_pack, b, current_seed, 'B')

                # Resize images based on destination size ready for pasting
                image_scale_ratio = target_image_width / image_a.size[0]
                target_image_height = round(image_a.size[1] * image_scale_ratio)
                image_a = image_a.resize((target_image_width, target_image_height))
                image_b = image_b.resize((target_image_width, target_image_height))

                # Calculate current row/col indices for positioning purposes
                row_index = floor(page_index / images_per_row)
                col_index = page_index % images_per_row 

                # Add image_a to page_a based on page_index
                y = mm_to_px(A4_MARGINS_MM, dpi) + row_index * (image_a.size[1] + image_spacing.y)
                x = centred_pos(page_middle_x, col_index, images_per_row, image_a.size[0], image_spacing.x)
                page_a.paste(image_a, (x, y), image_a)

                # Add to page_b based on page_index in REVERSE COLUMN ORDER
                # NOTE: positions reversed horizontally to support long edge duplex printing
                col_index = (images_per_row - 1) - col_index
                x = centred_pos(page_middle_x, col_index, images_per_row, image_b.size[0], image_spacing.x)
                page_b.paste(image_b, (x, y), image_b)
        
        print(f"Writing {output_filename}")
        pages[0].save(output_filename, 'pdf', resolution=dpi, save_all=True, append_images=pages[1:])


if __name__ == "__main__":
    cli()
