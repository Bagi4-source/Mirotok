import random
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
import os
import re
import matplotlib.pyplot as plt
import matplotlib.dates as dates
import matplotlib.ticker as ticker
from datetime import datetime, timedelta

DIR = 'bp_masks'
ARROWS_DIR = 'arrows'


def get_time(str_time):
    str_time = str_time.split('.')[0]
    return datetime.fromisoformat(str_time)


def generate_plot(data):
    X = []
    Y = []
    for item in data:
        Y.append(item.get('result'))
        X.append(get_time(item.get('create_time')))

    fig, ax = plt.subplots()

    ax.plot(X, Y, marker='o', linestyle='--', color='r')
    ax.plot(X, [-0.2] * len(X), linestyle='-', color='k', linewidth=1.8)

    for i, x in enumerate(X):
        y = Y[i]
        if i != len(X) - 1 and X[i] - X[i - 1] < timedelta(hours=1) or \
                len(X) >= 15 and X[i] - X[i - 1] < timedelta(hours=20):
            continue
        plt.annotate(f'{x.strftime("%H:%M")}',
                     xy=(x, y),
                     xytext=(x, 160),
                     fontsize=11, rotation=45)

    ax.xaxis.set_major_formatter(dates.DateFormatter('%d %b'))
    # ax.xaxis.set_major_locator(ticker.MultipleLocator(2 if max(X) - min(X) > timedelta(days=10) else 1))

    ax.yaxis.set_major_locator(ticker.MultipleLocator(4))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(19))

    ax.set_ylabel("%", fontsize=24, labelpad=140, rotation=0)

    ax.yaxis.set_label_coords(-0.02, 1.01)

    ax.minorticks_on()
    ax.grid(linestyle='-', linewidth=1.6)
    ax.grid(which='minor',
            color='gray',
            linestyle=':')
    fig.set_figwidth(12)
    fig.set_figheight(8)

    plt.xticks(rotation=45, fontsize=18)
    plt.yticks(rotation=0, fontsize=18)
    plt.xlim(max(max(X) - timedelta(days=31), min(X)), max(X))
    plt.ylim(-76, 152)

    bio = BytesIO()
    bio.name = 'image.png'
    plt.savefig(bio, format='png')
    bio.seek(0)
    return bio


def generate_image(positive, negative):
    image = Image.open(os.path.join(DIR, 'bg.png'))
    for item in positive:
        path = os.path.join(os.path.join(DIR, 'pink'), f'{item.upper()}.png')
        if os.path.exists(path):
            item = Image.open(path)
            image.paste(item, mask=item)

    for item in negative:
        path = os.path.join(os.path.join(DIR, 'blue'), f'{item.upper()}.png')
        if os.path.exists(path):
            item = Image.open(path)
            image.paste(item, mask=item)

    return image


async def bones_sum(selected_cards):
    bones = []
    for card in selected_cards:
        bones.extend([x for x in card.get('bones', []) if x not in bones])
    return bones


def get_degree(x):
    if x < 0:
        return f"{(abs(x) - 1) * 15}°"
    if x > 0:
        return f"{(x - 1) * 15}°"
    return '--'


def get_color(x):
    if x < 0:
        return (0, 163, 255)
    if x > 0:
        return (255, 153, 0)
    return (0, 0, 0)


def get_image(items):
    image = Image.open(os.path.join(ARROWS_DIR, 'bg.png'))
    for key, value in items.items():
        if value != 0:
            path = os.path.join(os.path.join(ARROWS_DIR, key), f'{value}.png')
            if os.path.exists(path):
                item = Image.open(path)
                image.paste(item, mask=item)
    imageDraw = ImageDraw.Draw(image)
    font = ImageFont.truetype(os.path.join(ARROWS_DIR, 'Inter.ttf'), 36)
    imageDraw.text((370, 840), f"ФБ\n{get_degree(items['ФБ'])}", fill=get_color(items['ФБ']), font=font, align="right")
    imageDraw.text((470, 840), f"СМ\n{get_degree(items['СМ'])}", fill=get_color(items['СМ']), font=font, align="left")
    imageDraw.text((370, 960), f"ЛР\n{get_degree(items['ЛР'])}", fill=get_color(items['ЛР']), font=font, align="right")
    imageDraw.text((470, 960), f"ЗД\n{get_degree(items['ЗД'])}", fill=get_color(items['ЗД']), font=font, align="left")
    return image


async def formula4(selected_cards):
    if len(selected_cards) != 5:
        return None
    positive = selected_cards[:3]
    negative = selected_cards[3:]

    result = {
        'ЛР': 0,
        'ЗД': 0,
        'СМ': 0,
        'ФБ': 0
    }

    for card in positive:
        EOB = card.get('EOB', [])
        for x in EOB:
            result[x] = result[x] + 1

    for card in negative:
        EOB = card.get('EOB', [])
        for x in EOB:
            result[x] = result[x] - 1

    positive = {}
    negative = {}

    for key, value in result.items():
        get_image(result).show()
        if value < 0:
            negative[key] = value
        if value > 0:
            positive[key] = value

    text = ''
    if negative:
        text += f'Скрытые потребности: {", ".join([f"{value}{key}" for key, value in negative.items()])}\n'

    if positive:
        text += f'Реальные потребности: {", ".join([f"{value}{key}" for key, value in positive.items()])}\n'

    image = get_image(result)
    bio = BytesIO()
    bio.name = 'image.png'
    image.save(bio, 'PNG')
    bio.seek(0)
    return bio, text


async def formula3(selected_cards):
    if len(selected_cards) != 5:
        return None
    positive = await bones_sum(selected_cards[:3])
    negative = await bones_sum(selected_cards[3:])

    pos_copy = positive.copy()
    neg_copy = negative.copy()

    for item in positive:
        if item in negative:
            pos_copy.remove(item)

    for item in negative:
        if item in positive:
            neg_copy.remove(item)

    img = generate_image(pos_copy, neg_copy)
    bio = BytesIO()
    bio.name = 'image.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio, positive


async def formula2(selected_cards):
    if len(selected_cards) != 5:
        return None
    positive = selected_cards[:3]
    negative = selected_cards[3:]

    result = 0
    for card in positive:
        power = card.get('power', 0)
        power = int(re.sub(r'\D', '', power))
        result += power

    for card in negative:
        power = card.get('power', 0)
        power = int(re.sub(r'\D', '', power))
        result -= power
    return result


async def formula1(selected_cards):
    if len(selected_cards) != 5:
        return None
    positive = selected_cards[:3]
    negative = selected_cards[3:]

    result = ''
    for card in positive:
        desc = card.get('desc', '')
        result += f'• НЕ {desc}\n'

    for card in negative:
        desc = card.get('desc', '')
        result += f'• {desc}\n'

    return result
