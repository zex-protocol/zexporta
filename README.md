
# Zellular Exchange Deposit

> [!NOTE]
Project Ownership Transition:
> This project was originally developed and maintained by **Zellular** under the MIT license until the end of 2024.
> As of **January 1, 2025**, ownership and further development of this project have been transferred to **Zex**.

> [!CAUTION]
> This code serves as a proof of concept (PoC) for the deposit and withdrawal module of the Zellular exchange. The Zellular exchange is an application designed as an example of interacting with the sequencer. **Do NOT use this code in production environments. It is intended for testnet use only.**


This is the deposit module for Zellular Exchange (ZEX), which monitores the deposit trasacion to ZEX wallets and employs Pyfrost to issue a schnorr signature. The highlevel structure of this module is demonstrated in the figure below:

![ZEX Deposit Structure](./imeges/zex-flow.png "Figure 1: ZEX Deposit Structure")
