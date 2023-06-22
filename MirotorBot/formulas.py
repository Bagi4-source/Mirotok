from io import BytesIO
import numpy as np
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


def get_percent(x):
    if x >= 19:
        return 7.35 - (x - 19) * 0.025
    if x <= -19:
        return 7.45 - (x + 19) * 0.025
    if x == 0:
        return 7.4
    return 7.4 + x * 0.05 / 19


def get_recommendation(selected_cards):
    recommendations = 'Рекомендация:\n'
    for card in selected_cards:
        recommendations += f"• {card.get('REC_RU', '')}\n\n"

    return recommendations


def generate_ph_plot(data):
    X = []
    Y = []
    for item in data:
        Y.append(get_percent(item.get('result')))
        X.append(get_time(item.get('create_time')))

    fig, ax = plt.subplots()
    ax.set_xlabel("График баланса кислотно-щелочной среды", fontsize=22, fontdict=dict(weight='medium'))

    alpha = 0.3
    ax.axhspan(get_percent(87), get_percent(152), facecolor='#E56635', alpha=alpha)
    ax.axhspan(get_percent(20), get_percent(87), facecolor='#FEFF58', alpha=alpha + 0.1)
    ax.axhspan(get_percent(0), get_percent(20), facecolor='#7ED265', alpha=alpha + 0.2)
    ax.axhspan(get_percent(-19), get_percent(0), facecolor='#69D07E', alpha=alpha + 0.2)
    ax.axhspan(get_percent(-48), get_percent(-19), facecolor='#689DCF', alpha=alpha)
    ax.axhspan(get_percent(-76), get_percent(-48), facecolor='#4E3975', alpha=alpha)

    ax.plot(X, Y, marker='o', linestyle='--', color='r', linewidth=2.6)
    ax.plot(X, [get_percent(-0.2)] * len(X), linestyle='-', color='g', linewidth=1.8)

    ax.xaxis.set_major_formatter(dates.DateFormatter('%d %b'))

    points = []
    for i in np.linspace(4.025, 7.4, num=9):
        points.append(i)
    for i in np.linspace(7.4, 8.875, num=5):
        points.append(i)

    ax.yaxis.set_major_locator(ticker.FixedLocator(points))

    ax.set_ylabel("pH", fontsize=24, labelpad=140, rotation=0)

    ax.yaxis.set_label_coords(-0.03, 1.03)
    ax.xaxis.set_label_coords(0.5, -0.05)

    ax.minorticks_on()
    ax.grid(linestyle='-', color='k', linewidth=1)
    ax.grid(which='minor', color='k', linestyle=':')
    fig.set_figwidth(12)
    fig.set_figheight(8)

    ax.xaxis.tick_top()
    plt.xticks(rotation=45, fontsize=18)
    plt.yticks(rotation=0, fontsize=18)
    ax.set_xlim(max(max(X) - timedelta(days=31), min(X)), max(X))
    ax.set_ylim(8.875, 4.025)

    bio = BytesIO()
    bio.name = 'image.png'
    plt.savefig(bio, format='png')
    bio.seek(0)
    return bio


def generate_plot(data):
    X = []
    Y = []
    for item in data:
        Y.append(item.get('result'))
        X.append(get_time(item.get('create_time')))

    fig, ax = plt.subplots()
    ax.set_xlabel("График баланса энергоемкости", fontsize=22, fontdict=dict(weight='medium'))

    ax.plot(X, Y, marker='o', linestyle='--', color='r', linewidth=2.6)
    ax.plot(X, [-0.2] * len(X), linestyle='-', color='k', linewidth=1.8)

    ax.xaxis.set_major_formatter(dates.DateFormatter('%d %b'))

    ax.yaxis.set_major_locator(ticker.MultipleLocator(4))
    ax.yaxis.set_major_locator(ticker.MultipleLocator(19))

    ax.set_ylabel("%", fontsize=24, labelpad=140, rotation=0)

    ax.yaxis.set_label_coords(-0.03, 1.03)
    ax.xaxis.set_label_coords(0.5, -0.05)

    ax.minorticks_on()
    ax.grid(linestyle='-', linewidth=1.6)
    ax.grid(which='minor',
            color='gray',
            linestyle=':')
    fig.set_figwidth(12)
    fig.set_figheight(8)

    ax.xaxis.tick_top()
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

    bg = Image.open(os.path.join(DIR, 'bg2.png'))
    bg.paste(image)

    return bg


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


def get_res_string(items, key):
    return f"{'ВП' if items[key] > 0 else 'НЗ' if items[key] < 0 else ''} {get_degree(items[key])}"


def get_image(items):
    image = Image.open(os.path.join(ARROWS_DIR, 'bg.png'))
    for key, value in items.items():
        if value != 0:
            path = os.path.join(os.path.join(ARROWS_DIR, key), f'{value}.png')
            if os.path.exists(path):
                item = Image.open(path)
                image.paste(item, mask=item)
            if value > 0:
                path = os.path.join(os.path.join(ARROWS_DIR, key), f'0.png')
                if os.path.exists(path):
                    item = Image.open(path)
                    image.paste(item, mask=item)
            else:
                path = os.path.join(os.path.join(ARROWS_DIR, key), f'-0.png')
                if os.path.exists(path):
                    item = Image.open(path)
                    image.paste(item, mask=item)

    imageDraw = ImageDraw.Draw(image)
    font = ImageFont.truetype(os.path.join(ARROWS_DIR, 'Inter.ttf'), 34)
    font.set_variation_by_name('Bold')

    def drawText(position, k):
        imageDraw.text(position, get_res_string(items, k), font=font, align="center", fill=(45, 45, 45))

    drawText((330, 890), 'ФБ')
    drawText((455, 890), 'СМ')
    drawText((330, 940), 'ЛР')
    drawText((455, 940), 'ЗД')

    bg = Image.open(os.path.join(ARROWS_DIR, 'bg2.png'))
    bg.paste(image)
    return bg


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
        if value < 0:
            negative[key] = value
        if value > 0:
            positive[key] = value

    text = []
    if positive:
        text.append(f'Реальные потребности: {", ".join([f"{value}{key}" for key, value in positive.items()])}')

    if negative:
        text.append(f'Скрытые потребности: {", ".join([f"({value}){key}" for key, value in negative.items()])}')

    text = "\n".join(text)
    text = 'Реальные и скрытые потребности:\n' + text

    image = get_image(result)
    bio = BytesIO()
    bio.name = 'image.png'
    image.save(bio, 'PNG')
    bio.seek(0)
    return bio, text


def sort_f(x):
    keys = {
        "C": 0,
        "T": 1,
        "L": 2,
        "S": 3
    }
    for key, value in keys.items():
        if x[0] == key:
            return int(x.replace(key, '').strip()) + value * 100
    return 0


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

    text = []
    if pos_copy:
        pos_copy = sorted(pos_copy, key=lambda x: sort_f(x))
        text.append(f"Реальные: {', '.join(pos_copy)}")
    if neg_copy:
        neg_copy = sorted(neg_copy, key=lambda x: sort_f(x))
        text.append(f"Скрытые: {', '.join(neg_copy)}")
    text = '\n'.join(text)

    img = generate_image(pos_copy, neg_copy)
    bio = BytesIO()
    bio.name = 'image.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio, text


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

    result = []
    for card in positive:
        desc = card.get('desc', '')
        result.append(f'• НЕ {desc}')

    for card in negative:
        desc = card.get('desc', '')
        result.append(f'• {desc}')

    result = '\n'.join(result)
    return result
