from django.contrib.auth.decorators import user_passes_test

def role_required(role):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.papel == role:
                return view_func(request, *args, **kwargs)
            else:
                return redirect('login')
        return _wrapped_view
    return decorator
