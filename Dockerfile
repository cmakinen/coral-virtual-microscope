FROM python:alpine

RUN apk update \
    && apk add wget build-base jpeg-dev zlib-dev openjpeg-dev tiff-dev glib-dev cairo-dev gdk-pixbuf-dev libxml2-dev sqlite-dev \
    && wget https://github.com/openslide/openslide/releases/download/v3.4.1/openslide-3.4.1.tar.gz \
    && pip install flask openslide-python \
    && tar -zxvf openslide-3.4.1.tar.gz \
    && cd openslide-3.4.1 \
    && ./configure \
    && make \
    && make install \
    && rm -rf openslide-3.4.1 openslide-3.4.1.tar.gz \
    && apk del wget build-base zlib-dev \
    && mkdir /openslide-app
COPY deepzoom_multiserver.py ./openslide-app/
RUN mkdir ./openslide-app/static
RUN mkdir ./openslide-app/templates
ADD static/ ./openslide-app/static
ADD templates/ ./openslide-app/templates

WORKDIR ./openslide-app/
CMD ["python", "deepzoom_multiserver.py", "-p", "80", "-l", "0.0.0.0", "/slides"]


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