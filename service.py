def pay(user):
    if user.is_active and not user.is_duplicate and not user.is_suspended:
        charge(user)
