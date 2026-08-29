import os
import glob
import re

template_files = glob.glob('app/templates/**/*.html', recursive=True)
updated_count = 0

for filepath in template_files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = re.sub(
        r'(<img\b(?!.*?referrerpolicy)[^>]*src=["\'][^"\']*(?:product|image_url|item\.product|p\.image_url|\{{|\${)[^"\']*["\'][^>]*)(>)',
        r'\1 referrerpolicy="no-referrer"\2',
        content
    )

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        updated_count += 1
        print(f"Updated: {filepath}")

print(f"Total template files updated with referrerpolicy: {updated_count}")
