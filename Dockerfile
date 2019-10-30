FROM gorialis/discord.py:minimal
WORKDIR /app
COPY requirements.txt ./
COPY config.json ./
COPY account.json ./
RUN pip3 install --no-cache-dir -i https://test.pypi.org/simple/ DoubleFault
CMD ["python3", "-m", "doublefault.dfbot", "--config=./config.json", "--account=./account.json"]
