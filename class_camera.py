# coding=utf-8
import cv2
import time
import mvsdk
import numpy as np
import platform

class camera(object):
    def __init__(self,default_exp_time):
        # 枚举相机
        DevList = mvsdk.CameraEnumerateDevice()
        nDev = len(DevList)
        if nDev < 1:
            print("No camera was found!")
            return

        for i, DevInfo in enumerate(DevList):
            print("{}: {} {}".format(i, DevInfo.GetFriendlyName(), DevInfo.GetPortType()))
        i = 0 if nDev == 1 else int(input("Select camera: "))
        DevInfo = DevList[i]
        print(DevInfo)

        # 打开相机
        self.hCamera = 0
        try:
            self.hCamera = mvsdk.CameraInit(DevInfo, -1, -1)
        except mvsdk.CameraException as e:
            print("CameraInit Failed({}): {}".format(e.error_code, e.message))
            return

        # 获取相机特性描述
        cap = mvsdk.CameraGetCapability(self.hCamera)

        # 判断是黑白相机还是彩色相机
        self.monoCamera = (cap.sIspCapacity.bMonoSensor != 0)

        # 黑白相机让ISP直接输出MONO数据，而不是扩展成R=G=B的24位灰度
        # if monoCamera:
        #    mvsdk.CameraSetIspOutFormat(hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO8)

        # 相机模式切换成连续采集
        mvsdk.CameraSetTriggerMode(self.hCamera, 0)

        # 手动曝光，曝光时间30ms
        mvsdk.CameraSetAeState(self.hCamera, 0)
        mvsdk.CameraSetExposureTime(self.hCamera, default_exp_time)


        # 设置12bit输出
        mvsdk.CameraSetMediaType(self.hCamera, 1)
        # 设置ISP 16位输出转numpy
        if self.monoCamera:
            mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_MONO16)
        else:
            mvsdk.CameraSetIspOutFormat(self.hCamera, mvsdk.CAMERA_MEDIA_TYPE_BAYGR16)

        #设置高低位
        #mvsdk.CameraSetRawStartBit(hCamera, 1)
        # 让SDK内部取图线程开始工作
        mvsdk.CameraPlay(self.hCamera)

        # 计算RGB buffer所需的大小，这里直接按照相机的最大分辨率来分配
        # FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * (1 if monoCamera else 3)
        FrameBufferSize = cap.sResolutionRange.iWidthMax * cap.sResolutionRange.iHeightMax * 3

        # 分配RGB buffer，用来存放ISP输出的图像
        # 备注：从相机传输到PC端的是RAW数据，在PC端通过软件ISP转为RGB数据（如果是黑白相机就不需要转换格式，但是ISP还有其它处理，所以也需要分配这个buffer）
        self.pFrameBuffer = mvsdk.CameraAlignMalloc(FrameBufferSize, 16)

    def set_exposure(self,t):
        mvsdk.CameraSetAeState(self.hCamera, 0)
        mvsdk.CameraSetExposureTime(self.hCamera, t)
        
        
    def capture(self):
        # 从相机取一帧图片
        try:
            pRawData, FrameHead = mvsdk.CameraGetImageBuffer(self.hCamera, 2000)

            # 12bit raw图像
            # if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO12_PACKED:
            #     print('12bit raw图像')
            #     status = mvsdk.CameraSaveImage(hCamera, "./test/raw16.raw", pRawData, FrameHead, mvsdk.FILE_RAW_16BIT, 100)
            # if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_BAYGB12_PACKED:
            #     print('12bit rgb raw图像')
            #     status = mvsdk.CameraSaveImage(hCamera, "./test/raw16rgb.raw", pRawData, FrameHead, mvsdk.FILE_RAW_16BIT, 100)
            # else:
            #     print('8bit raw图像')
            #     status = mvsdk.CameraSaveImage(hCamera, "./test/raw8.raw", pRawData, FrameHead, mvsdk.FILE_RAW, 100)

            mvsdk.CameraImageProcess(self.hCamera, pRawData, self.pFrameBuffer, FrameHead)
            mvsdk.CameraReleaseImageBuffer(self.hCamera, pRawData)
            #status = mvsdk.CameraSaveImage(self.hCamera, "./test/isp.bmp", self.pFrameBuffer, FrameHead, mvsdk.FILE_BMP, 100)

            # cv2 图像翻转
            if platform.system() == "Windows":
                mvsdk.CameraFlipFrameBuffer(self.pFrameBuffer, FrameHead, 1)

            # 12bit图像，转ISP后为，16bit图像 16转换numpy
            if FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_MONO16 :
                frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(self.pFrameBuffer)
                frame = np.frombuffer(frame_data, dtype=np.uint16)
                frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth))
                # 16bit的数据，转12bit
                #frame = frame / 16

                # 转8bit 图像，存图
                #frame = (frame / 256).astype('uint8')
                # new_uint16_img = frame.astype(np.uint8)
                #cv2.imwrite("./test/6.png", frame)
                #print(frame)
            elif FrameHead.uiMediaType == mvsdk.CAMERA_MEDIA_TYPE_BGR8:
                frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(self.pFrameBuffer)
                frame = np.frombuffer(frame_data, dtype=np.uint8)
                frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth,
                                    1 if self.monoCamera else 3))
                cv2.imwrite("./test/numpyBGR8.bmp", frame)
            else:
                frame_data = (mvsdk.c_ubyte * FrameHead.uBytes).from_address(self.pFrameBuffer)
                frame = np.frombuffer(frame_data, dtype=np.uint8)
                frame = frame.reshape((FrameHead.iHeight, FrameHead.iWidth,
                                    1 if self.monoCamera else 3))
                cv2.imwrite("./test/numpy8.bmp", frame)

        # frame = cv2.resize(frame, (640, 480), interpolation=cv2.INTER_LINEAR)
            
        except mvsdk.CameraException as e:
          print("CameraGetImageBuffer failed({}): {}".format(e.error_code, e.message))
        #convert 3d data to 2d

        return frame
    def release_buffer(self):
        mvsdk.CameraAlignFree(self.pFrameBuffer)
        
    def close(self):
    # # 关闭相机
        mvsdk.CameraUnInit(self.hCamera)

    # # 释放帧缓存
        mvsdk.CameraAlignFree(self.pFrameBuffer)
if __name__ == '__main__':
    h = camera(1000)
    h.set_exposure(3000)
    time.sleep(0.5)#must wait, otherwise parameter not implemented
    #for i in range(2):
    #frame = h.capture()
    frame = h.capture()
    img8 = (frame/256).astype('uint8')
    cv2.imshow("Press q to end", img8)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    h.close()
    
