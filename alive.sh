while true
do
    sleep $ALIVE_PING_TOUT
    wget -q -O/dev/null $BASE_URL_OF_BOT
    # 2020-08-23T16:01:18.877873+00:00 heroku[router]
    # 2020-08-23T16:26:18.954797+00:00 heroku[router]
    # working proof [value is 25m] 
done