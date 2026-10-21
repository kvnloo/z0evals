def matches(pattern, topic):
    p, t = pattern.split("."), topic.split(".")
    if p and p[-1] == "#":
        head = p[:-1]
        if len(t) <= len(head):
            return False
        t = t[:len(head)]
        p = head
    if len(p) != len(t):
        return False
    return all(a == "*" or a == b for a, b in zip(p, t))
