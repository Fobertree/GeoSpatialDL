import torchvision

data = torchvision.datasets.Places365('./Data', download=True)
print(data)