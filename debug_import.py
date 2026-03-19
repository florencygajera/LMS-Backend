"""Debug script to test imports"""
import os
os.environ['USE_SQLITE'] = 'true'

output = []

# Now import - settings should pick up the env variable
from common.core.config import settings
output.append(f'USE_SQLITE: {settings.USE_SQLITE}')
output.append(f'DATABASE_URL: {settings.DATABASE_URL}')

# Now check if the models are properly loaded
from common.core.database import Base
output.append(f'Base metadata tables before: {list(Base.metadata.tables.keys())}')

# Import models 
from services.auth_service.models.user import User
output.append(f'User class: {User}')
output.append(f'User.__tablename__: {User.__tablename__}')
output.append(f'Base metadata tables after: {list(Base.metadata.tables.keys())}')

# Print output
for line in output:
    print(line)
