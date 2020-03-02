FROM bitnami/minideb:buster

COPY requirements-all.txt .
RUN apt-get update -y \
    && apt-get install -y python3 python3-pip openslide-tools \
    && pip3 install -r requirements-all.txt --no-cache-dir \
    && apt-get remove -y python3-pip \
    && apt -y autoremove \
    && apt-get -y clean \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir /openslide-app
COPY app.py all_slides.db ./openslide-app/
RUN mkdir ./openslide-app/static
RUN mkdir ./openslide-app/templates
ADD static/ ./openslide-app/static
ADD templates/ ./openslide-app/templates

WORKDIR ./openslide-app/
CMD ["python3", "app.py", "-p", "80", "-l", "0.0.0.0", "/slides"]


# ec2 docker installation
###only on rhel... amzlinux doesn't need this
####### sudo yum install yum-utils
####### sudo yum-config-manager --enable rhui-REGION-rhel-server-extras
# sudo yum install docker -y
# sudo service docker start
#
# mkdir /home/ec2-user/slides
# mkfs -t ext4 /dev/sdf
# mount /dev/xvdf /home/ec2-user/slides

# docker run -p 80:80 -v /home/ec2-user/slides/:/slides:z docker.io/cmakinen/coral-vm:0.1 &