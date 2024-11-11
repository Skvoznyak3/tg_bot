import matplotlib.pyplot as plt
import io

def generate_chart(data, ticker):
    plt.plot(data['dates'], data['prices'])
    plt.title(f'Изменение цены {ticker}')
    plt.xlabel('Дата')
    plt.ylabel('Цена')
    image = io.BytesIO()
    plt.savefig(image, format='png')
    image.seek(0)
    return image
