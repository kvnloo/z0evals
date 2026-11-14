def summary(inv):
    lines = ["sku,on_hand,reserved,available"]
    for sku in inv.skus():
        lines.append(
            f"{sku},{inv.on_hand(sku)},{inv.reserved(sku)},{inv.available(sku)}"
        )
    return "\n".join(lines)
