import os
import re

def clean_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove 'import React' variants
    content = re.sub(r'import\s+React\s+from\s+[\'\"]react[\'\"];\n?', '', content)
    content = re.sub(r'import\s+React\s*,\s*\{\s*', 'import { ', content)

    # Specific unused variables
    if 'Header.tsx' in path:
        content = content.replace(\"import { Bell, Settings } from 'lucide-react';\", \"import { Bell } from 'lucide-react';\")
    elif 'ManualWorkspace.tsx' in path:
        content = content.replace('triggerSpike, triggerRandomSimulator', 'triggerRandomSimulator')
    elif 'NotificationPopover.tsx' in path:
        content = content.replace('const { notifOpen, setNotifOpen, refreshPulse } = useApp();', 'const { notifOpen, setNotifOpen } = useApp();')
    elif 'SmartWorkspace.tsx' in path:
        content = content.replace('const missedKey = useRef(0);\\n', '')
    elif 'WatchlistSidebar.tsx' in path:
        content = content.replace('addStockToWatchlist, removeStockFromWatchlist, createWatchlist', 'addStockToWatchlist, removeStockFromWatchlist')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

src_dir = 'c:/Users/sithi/OneDrive/Desktop/GROW/market-pulse/frontend/src'
for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith('.tsx') or file.endswith('.ts'):
            clean_file(os.path.join(root, file))
print('Imports cleaned.')
