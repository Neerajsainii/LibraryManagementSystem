from django.template.loader import get_template
from django.http import HttpResponse
from django.conf import settings
import os

def debug_template_dirs(request):
    template_name = 'base.html'
    debug_info = [
        "Template Search Paths:",
        "--------------------"
    ]
    
    # Add configured template directories
    for template_setting in settings.TEMPLATES:
        if template_setting['BACKEND'] == 'django.template.backends.django.DjangoTemplates':
            for template_dir in template_setting['DIRS']:
                path = str(template_dir)
                debug_info.append(f"DIRS: {path}")
                if os.path.exists(path):
                    debug_info.append(f"  Directory exists")
                    if os.path.exists(os.path.join(path, template_name)):
                        debug_info.append(f"  {template_name} exists in this directory")
                    else:
                        debug_info.append(f"  {template_name} NOT found in this directory")
                else:
                    debug_info.append(f"  Directory does NOT exist")

    # Add installed apps template directories if APP_DIRS is True
    if settings.TEMPLATES[0]['APP_DIRS']:
        debug_info.append("\nApp Template Directories:")
        debug_info.append("----------------------")
        for app in settings.INSTALLED_APPS:
            if '.' in app:
                app_name = app.split('.')[-1]
            else:
                app_name = app
            template_dir = os.path.join(settings.BASE_DIR, app_name, 'templates')
            if os.path.exists(template_dir):
                debug_info.append(f"App: {app}")
                debug_info.append(f"  Template dir: {template_dir}")
                if os.path.exists(os.path.join(template_dir, template_name)):
                    debug_info.append(f"  {template_name} exists in this directory")
                else:
                    debug_info.append(f"  {template_name} NOT found in this directory")

    return HttpResponse('<br>'.join(debug_info), content_type='text/plain')