import torch
state_dict = torch.load("./weight/ReID/osnet_x0_25_market_256x128_amsgrad_ep180_stp80_lr0.003_b128_fb10_softmax_labelsmooth_flip.pth")
torch.save(state_dict, './weight/ReID/osnet_x0_25_market.pt')