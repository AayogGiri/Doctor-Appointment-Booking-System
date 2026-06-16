from django.shortcuts import redirect


# =========================
# UNAUTHENTICATED USER ONLY
# (prevents logged-in users
# from accessing login/register)
# =========================
def unauthenticated_user(view_func):

    def wrapper_func(request, *args, **kwargs):

        if request.user.is_authenticated:
            # already logged in → redirect to role handler
            return redirect('to_user_login')

        return view_func(request, *args, **kwargs)

    return wrapper_func


# =========================
# ROLE REQUIRED DECORATOR
# (Doctor / Patient check)
# =========================
def allowed_users(allowed_roles=None):

    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):

        def wrapper_func(request, *args, **kwargs):

            group = None

            if request.user.groups.exists():
                group = request.user.groups.all()[0].name

            if group in allowed_roles:
                return view_func(request, *args, **kwargs)

            return redirect('home')

        return wrapper_func

    return decorator


# =========================
# SIMPLE LOGIN REQUIRED
# =========================
def login_required_simple(view_func):

    def wrapper_func(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect('login')

        return view_func(request, *args, **kwargs)

    return wrapper_func