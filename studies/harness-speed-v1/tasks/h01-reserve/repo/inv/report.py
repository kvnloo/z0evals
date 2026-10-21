def summary(inv):
    lines = ["sku,on_hand"]
    for sku in inv.skus():
        lines.append(f"{sku},{inv.on_hand(sku)}")
    return "\n".join(lines)
