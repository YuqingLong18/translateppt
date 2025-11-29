module.exports = {
  apps: [
    {
      name: 'translateppt',
      script: 'gunicorn',
      args: '-c /www/wwwroot/translateppt/gunicorn_config.py "backend.app:create_app()"',
      cwd: '/www/wwwroot/translateppt',
      interpreter: '/www/wwwroot/translateppt/venv/bin/python',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        PATH: '/www/wwwroot/translateppt/venv/bin:/usr/local/bin:/usr/bin:/bin',
        PYTHONUNBUFFERED: '1'
      },
      error_file: '/www/wwwroot/translateppt/logs/pm2-error.log',
      out_file: '/www/wwwroot/translateppt/logs/pm2-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true
    }
  ]
};

