def pay(user):
    if user.is_active and not user.is_cancelled and user.is_verified:  # Why-blame PR integration test
        charge(user)
