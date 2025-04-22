#!/bin/bash
XRAYZIP='https://github.com/XTLS/Xray-core/releases/download/v1.7.5/Xray-linux-64.zip'
WORKDIR='/xray'
yum install -y wget unzip screen
mkdir $WORKDIR
wget $XRAYZIP -O $WORKDIR/Xray.zip
unzip $WORKDIR/Xray.zip -d $WORKDIR/bin
cat > $WORKDIR/config.json << EOF
{0}
EOF
screen -dmS xray $WORKDIR/bin/xray -c $WORKDIR/config.json