import torch
import torch.nn as nn
from torchvision.utils import save_image
import numpy as np

from models.snn_gan import Generator, Discriminator
from utils.dataset import get_dataset

def main():
    n_epochs = 200
    batch_size = 64
    sample_interval = 400
    device = torch.device('cuda:1')
    dtype = torch.float
    noise_dim = 100
    num_steps = 25
    start_grad_step = 24

    train_loader,_ = get_dataset(batch_size, "mnist")

    generator = Generator(noise_dim=noise_dim,num_steps=num_steps).to(device=device, dtype=dtype)
    discriminator = Discriminator(num_steps=num_steps).to(device=device, dtype=dtype)
    optimizer_G = torch.optim.Adam(generator.parameters(), lr=1e-4)
    optimizer_D = torch.optim.Adam(discriminator.parameters(), lr=1e-4)
    loss = nn.BCELoss()

    for epoch in range(n_epochs):
        for i, (imgs, _) in enumerate(train_loader):
            valid = torch.ones((num_steps, imgs.shape[0], 1)).to(device=device, dtype=dtype)
            fake = torch.zeros((num_steps, imgs.shape[0], 1)).to(device=device, dtype=dtype)
            real_imgs = imgs.to(device=device, dtype=dtype)

            z = torch.tensor(np.random.normal(0, 1, (imgs.shape[0], noise_dim))).to(device=device, dtype=dtype)

            optimizer_G.zero_grad()
            gen_imgs = generator(z)
            g_loss = 0
            for step in range(start_grad_step, num_steps):
                g_loss += loss(discriminator(gen_imgs[step]), valid)
            g_loss = g_loss / (num_steps - start_grad_step)
            g_loss.backward()
            optimizer_G.step()

            optimizer_D.zero_grad()
            gen_imgs = gen_imgs.detach()
            d_loss = 0
            for step in range(start_grad_step, num_steps):
                real_loss = loss(discriminator(real_imgs.reshape(batch_size, -1)), valid)
                fake_loss = loss(discriminator(gen_imgs[step]), fake)
                d_loss += (fake_loss + real_loss) / 2
            d_loss = d_loss / (num_steps - start_grad_step)
            d_loss.backward()
            optimizer_D.step()

            print(
                "[Epoch %d/%d] [Batch %d/%d] [D loss: %f] [G loss: %f]"
                % (epoch, n_epochs, i, len(train_loader), d_loss.item() / 2, g_loss.item())
            )

            batches_done = epoch * len(train_loader) + i
            if batches_done % sample_interval == 0:
                image = gen_imgs.data[:, 0, ].reshape([num_steps, 1, 28, 28])
                save_image(image, "images/gan_%d.png" % batches_done, nrow=5, normalize=True,)

if __name__ == "__main__":
    main()