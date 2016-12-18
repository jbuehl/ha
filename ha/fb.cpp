// g++ -c -fPIC fb.cpp -o fb.o
// g++ -shared -Wl,-soname,libfb.so -o libfb.so fb.o

#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <linux/fb.h>
#include <sys/mman.h>
#include <sys/ioctl.h>

class FB{
    int fbfd = 0;
    struct fb_var_screeninfo vinfo;
    struct fb_fix_screeninfo finfo;
    int screensize;
    int bytesPerPixel;
    char* fbmap;
    public:
        int xRes;
        int yRes;
        int bitsPerPixel;
        FB(char* device) {
            // Open the file for reading and writing
            fbfd = open(device, O_RDWR);
            // Get fixed screen information
            ioctl(fbfd, FBIOGET_FSCREENINFO, &finfo);
            // Get variable screen information
            ioctl(fbfd, FBIOGET_VSCREENINFO, &vinfo);
            xRes = vinfo.xres;
            yRes = vinfo.yres;
            bitsPerPixel = vinfo.bits_per_pixel;
            // Figure out the size of the screen in bytes
            bytesPerPixel = vinfo.bits_per_pixel / 8;
            screensize = vinfo.xres * vinfo.yres * bytesPerPixel;
            // Map the device to memory
            fbmap = (char *)mmap(0, screensize, PROT_READ | PROT_WRITE, MAP_SHARED, fbfd, 0);
        }
        ~FB() {
            munmap(fbmap, screensize);
            close(fbfd);
        }
        int getXres() {
            return vinfo.xres;
        }
        int getYres() {
            return vinfo.yres;
        }
        int getBitsPerPix() {
            return vinfo.bits_per_pixel;
        }
        // move a pixel map to the specified location on the display
        // pixmap is 4 bytes per pixel - BGRT
        // offset, yoffset, width, and height are in pixels
        void setPixMap(int xoffset, int yoffset, int width, int height, char* pixmap) {
            int src = (int)pixmap;
            int srcIncr = width * bytesPerPixel;
            int dst = (int)fbmap + (xoffset + vinfo.xoffset) * bytesPerPixel + (yoffset + vinfo.yoffset) * finfo.line_length;
            int dstIncr = finfo.line_length;
            for (int y=0; y<height; y++) {
                // memcpy is safe because src and dst can't overlap
                memcpy((char*)dst, (char*)src, srcIncr);
                src += srcIncr;
                dst += dstIncr;
            }
        }
        // move a grayscale map to the specified location on the display
        // graymap is 1 byte per pixel
        // offset, yoffset, width, and height are in pixels
        void setGrayMap(int xoffset, int yoffset, int width, int height, char* graymap, char* fgcolor, char* bgcolor, int dstMap, int dstwidth, int dstheight) {
            int src = (int)graymap;
            int dst;
            int dstIncr;
            if (dstMap == 0) {
                dst = (int)fbmap + (xoffset + vinfo.xoffset) * bytesPerPixel + (yoffset + vinfo.yoffset) * finfo.line_length;
                dstIncr = finfo.line_length;
            } else {
                dst = (int)dstMap + xoffset * bytesPerPixel + yoffset * dstwidth * bytesPerPixel;
                dstIncr = dstwidth * bytesPerPixel;
            }
            for (int y=0; y<height; y++) {
                for (int x=0; x<width; x++) {
                    if (*(char*)src > 0x80) {
                        memcpy((char*)(dst + 4*x), fgcolor, 4);    
                    }
                    else {
                        memcpy((char*)(dst + 4*x), bgcolor, 4);    
                    }
                    src ++;
                }
                dst += dstIncr;
            }
        }
        // fill the frame buffer with the specified pixel map
        // assume fillpixel length is 4
        void fill(char* fillpixel) {
            for (int i=0; i<finfo.smem_len; i=i+4) {
                memcpy(fbmap+i, fillpixel, 4);
            }
        }
};

extern "C" {
    FB* init(char* device){ return new FB(device); }
    void del(FB* fb){ fb->~FB(); }
    int getXres(FB* fb){ fb->getXres(); }
    int getYres(FB* fb){ fb->getYres(); }
    int getBitsPerPix(FB* fb){ fb->getBitsPerPix(); }
    void setPixMap(FB* fb, int x, int y, int w, int h, char* pixmap)
        { fb->setPixMap(x, y, w, h, pixmap); }
    void setGrayMap(FB* fb, int x, int y, int w, int h, char* graymap, char* fgcolor, char* bgcolor, int dstMap, int dstwidth, int dstheight)
        { fb->setGrayMap(x, y, w, h, graymap, fgcolor, bgcolor, dstMap, dstwidth, dstheight); }
    int getMap(int size, char* fillpixel) {
        void* map = malloc(size);
        for (int i=0; i<size; i=i+4) {
            memcpy((char*)map+i, fillpixel, 4);
        }
        return (int)map; 
    }
    void freeMap(int map) { free((void*)map); }
    void fill(FB* fb, char* fillpixel){ fb->fill(fillpixel); }
}

