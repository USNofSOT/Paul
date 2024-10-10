#Function that specifies Discord ID's for NSC Engineers
def is_allowed_user(ctx):
    allowed_user_ids = [646516242949341236, 690264788257079439]
    return ctx.author.id in allowed_user_ids