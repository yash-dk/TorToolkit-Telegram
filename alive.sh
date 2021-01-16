while true
do
    sleep $ALIVE_PING_TOUT
    wget -q -O/dev/null $BASE_URL_OF_BOT
done