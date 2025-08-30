#!/usr/bin/env python3

import sys
sys.path.insert(0, 'src')

from config import Config
from pydantic import ValidationError
import tempfile
import os
from unittest.mock import patch

# Test empty URL
temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False)
temp_file.write('')
temp_file.close()

try:
    with patch.dict(os.environ, {}, clear=True):
        try:
            config = Config(_env_file=temp_file.name, supabase_url='', supabase_key='valid-key')
            print('Empty URL: No error - config created')
        except ValidationError as e:
            print('Empty URL ValidationError:', str(e))
        
        try:
            config = Config(_env_file=temp_file.name, supabase_url='invalid-url', supabase_key='valid-key')
            print('Invalid URL: No error - config created')
        except ValidationError as e:
            print('Invalid URL ValidationError:', str(e))
            
        try:
            config = Config(_env_file=temp_file.name, supabase_url='https://valid.supabase.co', supabase_key='')
            print('Empty key: No error - config created')
        except ValidationError as e:
            print('Empty key ValidationError:', str(e))
finally:
    os.unlink(temp_file.name)