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
from util import mm_to_px, chunk, Coords, Dimensions, centred_pos

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
    
    text_offset:Coords
    text_align:str
    text_colour:str

    tile_offset:Coords
    tile_spacing:Coords

    def __init__(self, name:str, config:dict) -> None:
        self.name = name
        
        self.font_file = config['font-file']
        self.font_size = config['font-size']
        self.text_offset = Coords.from_dict(config['text-offset'])
        self.text_colour = config['text-colour']
        self.text_align = TextAlign(config['text-align'] if 'text-align' in config else 'left')
        self.tile_offset = Coords.from_dict(config['tile-offset'])
        self.tile_spacing = Coords.from_dict(config['tile-spacing'])

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

class Layout:
    name:str
    page_size_mm:Dimensions
    page_margins_mm:int
    dpi:int
    rows:int
    cols:int
    card_size_mm:Dimensions
    card_spacing_mm:Dimensions
    crop_mark_size_mm:int
    crop_mark_colour:str
    bleed_size_mm:int
    bleed_colour:str

    def __init__(self, name:str, config:dict) -> None:
        self.name = name
        
        self.page_size_mm = Dimensions.from_dict(config['page-size-mm'])
        self.page_margins_mm = config['page-margins-mm']
        self.dpi = config['dpi']
        self.rows = config['rows']
        self.cols = config['cols']
        self.card_size_mm = Dimensions.from_dict(config['card-size-mm'])
        self.card_spacing_mm = Dimensions.from_dict(config['card-spacing-mm'])
        
        if 'crop-marks' in config:
            self.crop_mark_size_mm = config['crop-marks']['size-mm']
            self.crop_mark_colour = config['crop-marks']['colour']

        if 'bleed' in config:
            self.bleed_size_mm = config['bleed']['size-mm']
            self.bleed_colour = config['bleed']['colour']        
        

    @property
    def images_per_page(self) -> int:
        return self.rows * self.cols
    
    @property 
    def page_size_px(self) -> Dimensions:
        return Dimensions(
            mm_to_px(self.page_size_mm.w, self.dpi), 
            mm_to_px(self.page_size_mm.h, self.dpi)
        )
    
    @property 
    def page_margins_px(self) -> int:
        return mm_to_px(self.page_margins_mm, self.dpi)
    
    @property 
    def card_spacing_px(self) -> Dimensions:
        return Dimensions(
            mm_to_px(self.card_spacing_mm.w, self.dpi), 
            mm_to_px(self.card_spacing_mm.h, self.dpi)
        )
    
    def scale_to_card_width(self, image:Image.Image) -> Image.Image:
        # Resize images based on destination size ready for pasting
        card_width_px = mm_to_px(self.card_size_mm.w, self.dpi)
        image_scale_ratio = card_width_px / image.size[0]
        card_height_px = round(image.size[1] * image_scale_ratio)
        return image.resize((card_width_px, card_height_px))


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


def load_layout(name:str) -> Layout:
    with open(f'layouts/{name}.json') as f:
        config = json.loads(f.read())

    return Layout(name, config)



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
@click.option('--layout-config', '--layout', '-l', default='a4-8x2-68mm', help='Layout parameters.')
def pdf(count:int, seed:int, template:list[str], output_dir:str, layout_config:str):
    asset_packs = load_asset_packs(template)
    layout = load_layout(layout_config)

    page_dimensions = (layout.page_size_px.w, layout.page_size_px.h)
    page_middle_x = round(page_dimensions[0] / 2)

    for asset_pack in asset_packs:
        pages: list[Image.Image] = []
        page_a = None
        page_b = None

        output_filename = os.path.join(output_dir, f'{asset_pack.name}-{layout.name}.pdf')

        with click.progressbar(range(0, count), length=count, label=f"Generating {output_filename}") as images:

            for i in images:
                current_seed = seed + i
                random.seed(current_seed)

                (a, b) = generate_word_grids()
                check_grids(a, b)

                b = reverse_grid(b)

                page_index = i % layout.images_per_page
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
                image_a = layout.scale_to_card_width(image_a)
                image_b = layout.scale_to_card_width(image_b)

                # Calculate current row/col indices for positioning purposes
                row_index = floor(page_index / layout.cols)
                col_index = page_index % layout.cols 

                # Add image_a to page_a based on page_index
                y = layout.page_margins_px + row_index * (image_a.size[1] + layout.card_spacing_px.h)
                x = centred_pos(page_middle_x, col_index, layout.cols, image_a.size[0], layout.card_spacing_px.w)
                page_a.paste(image_a, (x, y), image_a)

                # Add to page_b based on page_index in REVERSE COLUMN ORDER
                # NOTE: positions reversed horizontally to support long edge duplex printing
                col_index = (layout.cols - 1) - col_index
                x = centred_pos(page_middle_x, col_index, layout.cols, image_b.size[0], layout.card_spacing_px.w)
                page_b.paste(image_b, (x, y), image_b)
        
        print(f"Writing {output_filename}")
        pages[0].save(output_filename, 'pdf', resolution=layout.dpi, save_all=True, append_images=pages[1:])


if __name__ == "__main__":
    cli()
