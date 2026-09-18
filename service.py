def pay(user):
    if user.is_active and not user.is_duplicate:
        charge(user)
