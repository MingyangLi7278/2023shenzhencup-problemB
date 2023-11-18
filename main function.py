#!/usr/bin/env python
# coding: utf-8

# In[3]:


from PIL import Image
import numpy as np
import math
import struct
import math
#用类来储存图片的一切数据（属性），定义对此图片的所有操作（类内函数）
class Picture:
    def __init__(self,file_path):
        self.file_path = file_path#要读取的JPG图片的位置 | 创建Picture实例时作为参数输入
        self.log = ""#含此JPG图片全部信息 | 执行self.init_necessary_infomation()获得
        self.hex_list = []#此JPG图片二进制层面数据 的 十六进制表示 | 执行self.init_necessary_infomation()获得
        self.departed_hex_list = []#将self.hex_list按照JPG文件结构分成12份,按索引0~11分别为：SOI,APP0,DQT,DQT,SOF,DHT,DHT,DHT,DHT,SOS,压缩数据,EOI | 执行self.init_necessary_infomation()获得
        self.quantumlization_table = []#分索引0和1储存两张量化表 | 执行self.init_necessary_infomation()获得
        self.qt_position = [[],[]]#用于<量化索引隐写>，表示各含64个量化系数的两张量化表，每个系数位置要隐写的 二进制数据形式隐藏数据 的位数 | 执行self.init_necessary_infomation()获得
        self.huffman_table = []#分索引0,1,2,3储存四张量化表,分别用于编码 Y_直流,Y_交流,CbCr_直流,CbCr交流 | 执行self.init_necessary_infomation()获得
        self.height = 0#图片垂直方向像素数量(高度) | 执行self.init_necessary_infomation()获得
        self.width = 0#图片水平方向像素数量(宽度) | 执行self.init_necessary_infomation()获得
        self.color_component_unit_flow = []#按"Y-Y-Y-Y-Cb-Cr循环"的顺序储存图片的颜色分量单元。每个元素代表1个颜色分量单元，1个颜色分量单元含64个已量化的颜色数据。是通过Huffman表解码JPG图片二进制层面数据流的"压缩数据区"得到的 | 执行get_huffman_decoding_res()获得
        self.reorganized_ccuf = [[],[],[]]#将color_component_unit_flow内的所有颜色分量单元按索引0,1,2 分 Y,Cb,Cr 三通道储存 | 执行self.read()获得
        self.DCT_list = []#图片在频域上(区别于空间域,注:空间域的颜色数据可以通过"离散余弦变换"转为频域)的颜色数据，按索引0,1,2 分 Y,Cb,Cr 三通道储存。是通过将每个颜色分量单元"反Z型编码"和"反量化"得到的 | 执行self.get_iquantumlize_izigzag_res()获得
        self.higher_base_code = []#隐藏数据(汉字)的gbk编码的高进制形式 | 执行self.get_higher_base_coding()获得
        self.message_bin_code = ""#隐藏数据(汉字)的gbk编码的二进制形式 | 执行self.get_higher_base_coding()获得
        self.qt_departed_message_bin_code = []#用于<量化索引隐写>，依照self.qt_position对self.message_bin_code进行分割 | 执行self.qt_write()获得
        self.requantumlized_color_component_unit_flow = []#储存用"修改后的量化表"进行重新量化后的颜色分量单元，结构同self.color_component_unit_flow | 执行self.get_zigzag_quantumlize_res()获得
        self.reorganized_rccuf = [[],[],[]]#将self.requantumlized_color_component_unit_flow内的所有颜色分量单元按索引0,1,2 分 Y,Cb,Cr 三通道储存，结构同self.reorganized_ccuf | 执行self.get_zigzag_quantumlize_res()获得
        self.huffman_code_flow = []#储存依照Huffman表编码的所有颜色分量单元数据，按"Y-Y-Y-Y-Cb-Cr循环"的顺序储存。是通过将reorganized_rccuf的Y,Cb,Cr三通道数据分别进行Huffman编码并按"Y-Y-Y-Y-Cb-Cr循环"的顺序重新组织得到的 | 执行self.get_huffman_coding_res()获得
        self.message = ""#储存从图片中读取(解隐写)出来的隐藏信息 | 执行self.read()或self.qt_read()均可获得
        self.img_r = []
        self.img_g = []
        self.img_b = []
        self.img_Y = []
        self.img_Cb = []
        self.img_Cr = []
        self.reduced_Cr = []#经过缩减采样后的Cr
        self.reduced_Cb = []
        self.Y_DCT = [] #Y通道不可能被缩减取样，这里就直接初始化了
        self.Cb_DCT = [] #Cb通道都会被缩减取样，初始化放在DCT函数下，size和self.reduced_Cb一样
        self.Cr_DCT = [] #Cr通道都会被缩减取样，初始化放在DCT函数下，size和self.reduced_Cr一样
        
    #函数功能：将self.hex_list按照JPG文件结构分成12份,按索引0~11分别为：SOI,APP0,DQT,DQT,SOF,DHT,DHT,DHT,DHT,SOS,压缩数据,EOI
    def get_departed_hex_list(self):
        import numpy as np
        import math
        #函数功能：输入十六进制数列表和索引，取得二进制数
        def hex2bin(hex_content,index=None):
            if index == None:#这种方式是直接把 一个 十六进制字符串转二进制，hex_content要传入 字符串
                hex_part = hex_content
                dec_num = int(hex_part,16)
                bin_num = bin(dec_num)
                bin_num2 = "{:0>8}".format(bin_num.lstrip("0b"))
                if len(bin_num2) != 8:
                    print("这个bin长度不是8")
                return bin_num2#输出 代表二进制数的 字符串
            else:#这种方式是把 列表中某个 十六进制字符串 元素 转二进制，hex_content要传入 以字符串为元素的列表，即['str','str', ... ]
                hex_part = hex_content[index]
                dec_num = int(hex_part,16)
                bin_num = bin(dec_num)
                bin_num2 = "{:0>8}".format(bin_num.lstrip("0b"))
                print(bin_num2)
                return bin_num2#输出 代表二进制数的 字符串 

        #函数功能：将 图片名.jpg 读取为十六进制，用列表含字符串的方式存储
        def read_file_as_hex(file_path):
            with open(file_path, 'rb') as f:
                file_content = f.read()
            hex_content = ''.join([hex(byte)[2:].zfill(2) for byte in file_content])
            hex_list = []
            bin_list = []
            for i in range(0,len(hex_content),2):
                hex_list.append(hex_content[i:i+2])
                bin_list.append(hex2bin(hex_content[i:i+2]))
            return hex_content,hex_list,bin_list

        hex_content,hex_list,bin_list = read_file_as_hex(self.file_path)
        self.hex_list = hex_list

        #函数功能：从列表中找出某一值对应的所有索引
        def find_indexes(lst, value):
            indexes = [i for i, x in enumerate(lst) if x == value]
            return indexes

        #函数功能：按照JPG标识头，分割hex_list
        def depart_hex_list(hex_lst,ff_indexes):
            end_of_meta = hex_content.find("003f00")#EOM
            end_of_meta = int(end_of_meta/2)
            for k in range(len(ff_indexes)):
                if ff_indexes[k] >= end_of_meta:
                    index_EOM = k-1#表示EOM所在的 jpg文件标识数据的 开头所在的 index在ff_indexes中所对应的索引
                    break
            #接下来删除ff_indexes中从索引index_EOM+1 至 索引-2所对应的元素
            len_original_ff = len(ff_indexes)-1
            #print(index_EOM,len_original_ff)
            for j in range(index_EOM+1,len_original_ff):
                del ff_indexes[index_EOM+1]
            #接下来把"003f00"的第二个00对应的索引，插入在ff_indexes的倒二位
            ff_indexes.insert(-1,end_of_meta+3)
            #print(ff_indexes)
            departed_hex_list = []
            for i in range(len(ff_indexes)-1):
                departed_hex_list.append(hex_lst[ff_indexes[i]:ff_indexes[i+1]])
            departed_hex_list.append(hex_lst[ff_indexes[-1]:])
            return departed_hex_list
        ff_indexes = find_indexes(hex_list,'ff')
        self.departed_hex_list = depart_hex_list(hex_list,ff_indexes)
        
    #函数功能：从self.departed_hex_list中获取图片各信息。
    def get_infomation(self):
        #函数功能：十六进制转二进制
        def hex2bin(hex_content,index=None):
            if index == None:#这种方式是直接把 一个 十六进制字符串转二进制，hex_content要传入 字符串
                hex_part = hex_content
                dec_num = int(hex_part,16)
                bin_num = bin(dec_num)
                bin_num2 = "{:0>8}".format(bin_num.lstrip("0b"))
                if len(bin_num2) != 8:
                    print("这个bin长度不是8")
                return bin_num2#输出 代表二进制数的 字符串
            else:#这种方式是把 列表中某个 十六进制字符串 元素 转二进制，hex_content要传入 以字符串为元素的列表，即['str','str', ... ]
                hex_part = hex_content[index]
                dec_num = int(hex_part,16)
                bin_num = bin(dec_num)
                bin_num2 = "{:0>8}".format(bin_num.lstrip("0b"))
                print(bin_num2)
                return bin_num2#输出 代表二进制数的 字符串 
        #一下定义的6个函数是：根据不同JPG标识头分别构造的解释器
        #1.SOI
        def SOI(soi_lst):#参数：代表SOI数据的列表
            if soi_lst[0] == 'ff' and soi_lst[1] == 'd8':
                self.log += "SOI,head of JPG."
            else:
                print("not SOI")

        #2.APP0
        def APP0(app0_lst):#参数：代表APP0数据的列表
            log = ""
            #验证是不是APP0
            if app0_lst[0] == 'ff' and app0_lst[1] == 'e0':
                log = log+"APP0\t"
            else:
                log = log+"not APP0\t"
                print(log)
                return 0
            #读取段长度，字节2~3
            app0_len = int(app0_lst[3],16)
            log += f"段长度:{app0_len}\t"
            #读取固定字符串，字节4~8
            for i in range(4,9):
                app0_const = chr(int(app0_lst[i],16))
                log += app0_const
            log += "\t"
            #读取主版本号、副版本号，字节9、10
            log += f"主版本号:{app0_lst[9]}\t副版本号:{app0_lst[10]}\t"
            #读取密度单位，字节11
            log += "密度单位:"
            if app0_lst[11] == '00':
                log += "无单位\t"
            elif app0_lst[11] == '01':
                log += "点数/英寸\t"
            elif app0_lst[11] == '02':
                log += "点数/厘米\t"
            else:
                log += "ERROR\t"
            #读取X、Y方向像素密度，字节12 13，14 15
            log += f"水平方向像素密度:{int(app0_lst[13],16)}\t垂直方向像素密度:{int(app0_lst[15],16)}\t"
            #读取略缩图X、Y方向像素数目，字节16、17
            x_thumbnail = int(app0_lst[16],16)
            y_thumbnail = int(app0_lst[17],16)
            log += f"略缩图水平像素数目:{x_thumbnail}\t略缩图垂直像素数目:{y_thumbnail}\t"
            if x_thumbnail > 0 and y_thumbnail > 0:
                log += "略缩图数据待读取"
            self.log += log
            #print(log)

        #3.DQT
        def DQT(dqt_lst):#参数：代表DQT数据的列表
            log = ""
            #验证是不是DQT
            if dqt_lst[0] == 'ff' and dqt_lst[1] == 'db':
                log = log+"DQT\t"
            else:
                log = log+"not DQT\t"
                print(log)
                return 0
            #读取段长度，字节2~3
            dqt_len = int(dqt_lst[2]+dqt_lst[3],16)
            log += f"段长度:{dqt_len}\t"
            #读取精度，字节4
            dqt_4 = "{:0>8}".format(bin(int(dqt_lst[4],16)).lstrip("0b"))
                #4 bits | 精度（0：8位、1：16位）
                #4 bits | 量化表ID，一般有2张，最多4张，取值 0~3
            log += f"QT精度:"
            dqt_precision = int(dqt_4[0:4],2)
            if dqt_precision == 0:
                log += "8位\t"
            else:
                log += "16位\t"

            log += f"QT号:{int(dqt_4[4:8],2)}\t" 
            self.log += log
            #print(log)
            #读取量化表，字节5~68 或 5~132，视dqt_precision而定
            dqt_label = []
            if dqt_precision == 0:
                for i in range(5,69):
                    dqt_label.append(int(dqt_lst[i],16))
                return dqt_label
            else:
                for i in range(5,132):
                    dqt_label.append(int(dqt_lst[i],16))
                return dqt_label

        #4.SOF0 图像帧
        def SOF0(sof0_lst):#参数：代表DQT数据的列表
            log = ""
            #验证是不是SOF0
            if sof0_lst[0] == 'ff' and sof0_lst[1] == 'c0':
                log = log+"SOF0\t"
            else:
                log = log+"not SOF0\t"
                print(log)
                return 0
            #读取段长度，字节2~3
            sof0_len = int(sof0_lst[2]+sof0_lst[3],16)
            log += f"段长度:{sof0_len}\t"
            #每个数据样本位数，字节4
            log += f"每个数据样本位数:{int(sof0_lst[4],16)}\t"
            #图像高度，宽度。字节5~6 和 7~8
            sof0_height = int(sof0_lst[5]+sof0_lst[6],16)
            sof0_width = int(sof0_lst[7]+sof0_lst[8],16)
            log += f"图像高度:{sof0_height}\t图像宽度:{sof0_width}\t"
            #读取颜色分量数，字节9
            color_num = int(sof0_lst[9],16)
            log += f"颜色分量数:{color_num}\n"
            color = []
            for i in range(color_num):
                color_id = sof0_lst[10+i*3]
                color_factor = hex2bin(sof0_lst[10+i*3+1])
                color_factor_x = int(color_factor[0:4],2)
                color_factor_y = int(color_factor[4:8],2)
                dqt_id = int(sof0_lst[10+i*3+2],16)
                color_component = []
                color_component.append(color_id)
                color_component.append(color_factor_x)
                color_component.append(color_factor_y)
                color_component.append(dqt_id)
                color.append(color_component)
                log += f"颜色ID:{color[i][0]}--水平采样因子:{color[i][1]}--垂直采样因子:{color[i][2]}--使用的QT表:{color[i][3]}\n"
            log.rstrip("\n")
            self.log += log
            #print(log)
            return color,sof0_height,sof0_width

        #5.DHT 哈夫曼表
        def DHT(dht_lst):#参数：代表DQT数据的列表
            log = ""
            #验证是不是DHT
            if dht_lst[0] == 'ff' and dht_lst[1] == 'c4':
                log = log+"DHT\t"
            else:
                log = log+"not DHT\t"
                print(log)
                return 0
            #读取段长度，字节2~3
            dht_len = int(dht_lst[2]+dht_lst[3],16)
            log += f"段长度:{dht_len}\t"
            #读取霍夫曼表类型，表ID。字节4，分前4bit和后4bit
            dht_factor = hex2bin(dht_lst[4])
            dht_class = int(dht_factor[0:4],2)
            dht_id = int(dht_factor[4:8],2)
            if dht_class == 0:
                log += "直流\t"
            elif dht_class == 1:
                log += "交流\t"
            log += f"哈夫曼表ID:{dht_id}\t"
            #读取哈夫曼表不同位数的码字数量，字节5~20
            num_per_position = []
            for i in range(16):
                num_per_position.append(int(dht_lst[i+5],16))
            #print(num_per_position)
            #读取哈夫曼各 位 的码的内容，字节20+1~20+sum(num_per_position)
            huffman_table = []
            count = 0
            for i in range(16):
                #print(f"time{i}")
                huffman_table.append([])
                huffman_table[-1].append(num_per_position[i])
                if num_per_position[i] == 0:
                    continue
                else:
                    for j in range(num_per_position[i]):
                        lst0 = []
                        lst0.append(dht_lst[21+count+j])
                        huffman_table[-1].append(lst0)
                count += num_per_position[i]
            self.log += log
            #print(log)
            def do_bin_str(bin_str):
                bin_lst = []
                for i in range(len(bin_str)):
                    bin_lst.append(bin_str[i])
                #print(bin_lst)
                for i in range(len(bin_lst)):#01101  011101
                    if bin_lst[-i-1] == "0":
                        bin_lst[-i-1] = "1"
                        break
                    elif bin_lst[-i-1] == "1":
                        bin_lst[-i-1] = "0"
                #print(bin_lst)
                res = ""
                for i in range(len(bin_lst)):
                    res += bin_lst[i]
                return res
            def generate_huffman_table(hfm_table):#输入通过DHT()函数返回得到的哈夫曼表
                coding = ""
                for i in range(16):#根据哈夫曼编码的定义，此哈夫曼表永远只含16个元素
                    position_coding_num = hfm_table[i][0]# 含i+1位的 编码 上 定义的 编码个数
                    coding += "0"
                    if position_coding_num == 0:
                        continue
                    else:
                        for j in range(len(hfm_table[i])-1):
                            hfm_table[i][j+1].append(coding)
                            coding = do_bin_str(coding)
            generate_huffman_table(huffman_table)
            return huffman_table

        #6.SOS 扫描行
        def SOS(sos_lst):#参数：代表SOS数据的列表
            log = ""
            #验证是不是SOS
            if sos_lst[0] == 'ff' and sos_lst[1] == 'da':
                log = log+"SOS\t"
            else:
                log = log+"not SOS\t"
                print(log)
                return 0
            #读取段长度，字节2~3
            sos_len = int(sos_lst[2]+sos_lst[3],16)
            log += f"段长度:{sos_len}\t"
            #读取颜色分量数，字节4
            color_num = int(sos_lst[4],16)
            log += f"颜色分量数:{color_num}\n"
            #读取各颜色分类对应的哈夫曼表 类型 及 ID
            color = []
            for i in range(color_num):
                color_id = sos_lst[5+i*2]
                color_factor = hex2bin(sos_lst[5+i*2+1])
                color_DC = int(color_factor[0:4],2)
                color_AC = int(color_factor[4:8],2)
                color_component = []
                color_component.append(color_id)
                color_component.append(color_DC)
                color_component.append(color_AC)
                color.append(color_component)
                log += f"颜色ID:{color[i][0]}--其DC使用的哈夫曼表ID:{color[i][1]}--其交流使用的哈夫曼表ID:{color[i][2]}\n"
            log.rstrip("\n")
            log += f"用途不明的三字节{sos_lst[5+2*color_num:5+2*color_num+3]}"
            self.log += log
            #print(log)
        SOI(self.departed_hex_list[0])
        APP0(self.departed_hex_list[1])
        self.quantumlization_table.append(DQT(self.departed_hex_list[2]))
        self.quantumlization_table.append(DQT(self.departed_hex_list[3]))
        color,height,width = SOF0(self.departed_hex_list[4])
        self.width = math.ceil(width/16)*16
        self.height = math.ceil(height/16)*16
        self.huffman_table.append(DHT(self.departed_hex_list[5]))
        self.huffman_table.append(DHT(self.departed_hex_list[6]))
        self.huffman_table.append(DHT(self.departed_hex_list[7]))
        self.huffman_table.append(DHT(self.departed_hex_list[8]))
        SOS(self.departed_hex_list[9])
        
    #函数功能：定义<量化系数隐写>时，两量化表各位置要隐写入的 二进制位数
    def get_qt_steganography_position(self):
        self.qt_position[0].extend([3]*13)
        self.qt_position[0].extend([4]*8)
        self.qt_position[0].extend([5]*23)
        self.qt_position[0].extend([6]*20)
        self.qt_position[1].extend([3]*3)
        self.qt_position[1].extend([4]*6)
        self.qt_position[1].extend([5]*5)
        self.qt_position[1].extend([6]*50)
    
    #函数功能：获取图片所有必要信息
    def init_necessary_infomation(self):
        self.get_departed_hex_list()
        self.get_infomation()
        self.get_qt_steganography_position()
        
    #函数功能：<标准码解释器>，依照JPG官方提供的标准码表，将二进制字符串 转 整数
    def std_coding_bin2int(self,bin_str):#输入二进制字符串，根据JPG提供的标准码表，搜寻并返回对应整数
        posi_or_negetive = int(bin_str[0],2) #为1表示正数，为0表示负数
        if posi_or_negetive == 1:
            sum_ = 0
            for i in range(len(bin_str)):
                sum_ += int(bin_str[-i-1],2)*2**i
            return sum_
        elif posi_or_negetive == 0:
            sum_ = 0
            for i in range(len(bin_str)):
                sum_ += abs(int(bin_str[-i-1],2)-1)*2**i
            sum_ = -sum_
            return sum_
        else:
            print("请输入 只含0和1的 二进制字符串")
            return None
        
    #函数功能：<标准码生成器>，依照JPG官方提供的标准码表，将整数 转 二进制字符串
    def std_coding_int2bin(self,val):#输入整数，根据JPG提供的标准码表，搜寻并返回对应二进制字符串
        code = ""
        position_num = 0
        while 2**position_num-1 < abs(val):
            position_num += 1
        rest_val = abs(val)
        for i in range(position_num):
            position_val = "0"#只能是0或1
            if 2**(position_num-1-i) <= rest_val:
                position_val = "1"
                rest_val -= 2**(position_num-1-i)
            else:
                position_val = "0"
                rest_val -= 0
            code += position_val
        #进行负数兼容
        neg_code = ""
        if val < 0:
            for i in range(len(code)):
                if code[i] == "0":
                    neg_code += "1"
                else:
                    neg_code += "0"
            code = neg_code
        return code
    
    #函数功能：根据Huffman表解码JPG压缩数据，获得Y,Cb,Cr三通道的"颜色分量单元"数据
    def get_huffman_decoding_res(self):
        #接下来根据哈夫曼表解码各通道"颜色分量单元"
        #函数功能：输入十六进制序列、索引，取得二进制数
        def hex2bin(hex_content,index=None):
            if index == None:#这种方式是直接把 一个 十六进制字符串转二进制，hex_content要传入 字符串
                hex_part = hex_content
                dec_num = int(hex_part,16)
                bin_num = bin(dec_num)
                bin_num2 = "{:0>8}".format(bin_num.lstrip("0b"))
                if len(bin_num2) != 8:
                    print("这个bin长度不是8")
                return bin_num2#输出 代表二进制数的 字符串
            else:#这种方式是把 列表中某个 十六进制字符串 元素 转二进制，hex_content要传入 以字符串为元素的列表，即['str','str', ... ]
                hex_part = hex_content[index]
                dec_num = int(hex_part,16)
                bin_num = bin(dec_num)
                bin_num2 = "{:0>8}".format(bin_num.lstrip("0b"))
                print(bin_num2)
                return bin_num2#输出 代表二进制数的 字符串 
            
        #函数功能：从列表中找出某一值对应的所有索引
        def find_indexes(lst, value):
            indexes = [i for i, x in enumerate(lst) if x == value]
            return indexes
        
        #self.departed_hex_list[10]为十六进制形式的压缩数据，但压缩数据的真正编码方式是“Huffman编码”结合“RL编码”。所以先把self.departed_hex_list[10]转换为单纯的无意义0和1字符串
        #函数功能：把十六进制形式的压缩数据转化为 无意义0和1字符串
        def element_merge(lst):
            #先找出所有ff00，然后去除00
            indexes = find_indexes(lst,"ff")
            for i in range(len(indexes)):
                del lst[indexes[-i-1]+1]
            #print(lst)
            merged_str = ""
            for i in range(len(lst)):
                merged_str += hex2bin(lst[i])
            return merged_str
        
        #函数功能：<哈夫曼编码查找器>，输入Huffman编码，查找Huffman表，获取此编码代表的权值。("权值"表示读取完此Huffman编码后，要往后读取几位二进制数字作为标准码。标准码代表的值就是1个已量化的频域上的颜色数据)
        def huffman_find(hfm_table,bits):
            for i in range(len(hfm_table)):
                if len(hfm_table[i]) == 1:#这种情况是没有 i+1 位的编码。i从0开始
                    continue
                for j in range(len(hfm_table[i])-1):
                    #print(hfm_table[i][j+1][1])
                    if hfm_table[i][j+1][1] == bits:
                        return int(hfm_table[i][j+1][0],16) #此返回的值代表要往后找多少位以匹配标准码表
            #若能在hfm_table找到bits，那么函数在循环中就会返回。若直到循环执行完了都还没返回，说明找不到
            #print(f"not found any {bits} in this hfm_table\n")
            return -1

        #函数功能：Huffman解码器，解码Huffman编码，执行结束返回 1个颜色分量单元
        def huffman_decoding(bin_str,hfm,hfm_ac,point,last_DC):#传入代表二进制序列的 字符串，即上面所得的merged_bin
            data = []
            #此为DC解码器
            do_DC = 1
            while do_DC == 1:
                do_DC = 0
                accumulate_bits = ""
                std_coding_len = 0
                #point = 0#作指针用，指明已经遍历到bin_str哪个位置了
                for head_bit in range(100):#括号内原本是len(bin_str)
                    #print(f"head_bit{head_bit}")
                    accumulate_bits += bin_str[point+head_bit]
                    if accumulate_bits == "1111111100000000":
                        print("0xFF00")
                        point += 15
                        data.append(255+last_DC)#255的十六进制是0xFF
                        std_coding_len == -4
                        break
                    #验证accumulate_bits是否是某一个哈夫曼编码，需要编一个函数，名为哈夫曼编码查找器。
                    std_coding_len = huffman_find(hfm,accumulate_bits)
                    if std_coding_len != -1:#accumulate_bits对应的哈夫曼编码找到了
                        point += head_bit
                        #print(f"hfm编码位数{head_bit+1},hfm编码内容{accumulate_bits}")
                        break
                    elif std_coding_len == -1 and len(accumulate_bits) == 16 and accumulate_bits[0:8] == "11111111":
                        print(f'FF后数值非00，也不构成RSTn，忽略此ff。point：{point}')
                        point += 8
                        do_DC = 1
                        std_coding_len = -4
                        break

                if std_coding_len != -4:
                    if std_coding_len == -1:
                        #print(f"accumulate_bits累积到了100位也没找到匹配的hfm编码")
                        return -2
                    #print(f"标准码位数{std_coding_len},标准码内容{bin_str[point+1:point+1+std_coding_len]}")
                    #接下来跟据std_coding_len查找编码，找到的编码对应标准码表，以解出直流差值diff
                    if std_coding_len == 0:
        #                print("此直流与同分量 上一直流 差值为0")
                        data.append(last_DC)
        #                print(f"指针现在在第{point}位(从0开始)")
                    else:
                        diff = self.std_coding_bin2int(bin_str[point+1:point+1+std_coding_len])
                        point += std_coding_len
        #                print(f"指针现在在第{point}位(从0开始)")
        #                print(f"解码得出 DC{diff+last_DC}")
                        data.append(diff+last_DC)
        #                print(data[0])


            #接下来编AC解码器,要循环直到EOB
            while True:
                point += 1#从上一编码的最后一位 移到 此编码的第一位
                accumulate_bits_ac = ""
                zeros_and_std = 0
                for head_bit in range(100):#括号内原本是len(bin_str)
                    #print(f"head_bit{head_bit}")
                    accumulate_bits_ac += bin_str[point+head_bit]
                    if accumulate_bits_ac == "1111111100000000":
                        print("0xFF00")
                        point += 15
                        data.append(255)#255的十六进制是0xFF
                        zeros_and_std == -4
                        break
                    #验证accumulate_bits是否是某一个哈夫曼编码，需要编一个函数，名为哈夫曼编码查找器。
                    zeros_and_std = huffman_find(hfm_ac,accumulate_bits_ac)
        #            print(f"zeros_and_std:{zeros_and_std}")
                    if zeros_and_std != -1:#accumulate_bits对应的哈夫曼编码找到了
                        point += head_bit
                        #print(f"\tAC的hfm编码位数{head_bit+1},hfm编码内容{accumulate_bits_ac}")
                        break

                if zeros_and_std == -4:
                    if len(data) < 64:
                        continue
                    elif len(data) == 64:
                        break
                else:
                    zeros_and_std = "{:0>2}".format(hex(zeros_and_std).lstrip("0x"))
        #            print(f"zeros_and_std:{zeros_and_std}")
                    zero_num = int(zeros_and_std[0],16)
                    std_num = int(zeros_and_std[1],16)
                    #接下来跟据std_num查找编码，找到的编码对应标准码表，以解出 交流幅值
                    #print(f"前零数{zero_num},标准码位数{std_num},标准码编码内容{bin_str[point+1:point+1+std_num]}")
                    if zero_num == 0 and std_num == 0:
        #                print("EOB")
                        #data补足0
                        for b in range(64-len(data)):
                            data.append(0)
        #                print(f"data长度{len(data)}")
                        break
                    elif zero_num == 15 and std_num == 0:#这是当非末尾连续0大于16个时，表示16个0为一组。hfm查找到的是'F0'
                        #print(f"连续16个非末尾0，point={point}")
                        if 64-len(data) <= 16:
                            #print(data)
                            #print(f"len_data={len(data)}前零数及标准码位数组合为 F0，表示非末尾16个连续的0，不可能出现在此位置。因为此颜色分量单元剩余空位不超过17个")
                            return -3
                        else:
                            for g in range(16):
                                data.append(0)
                            point += 0
                    else:
                        ac = self.std_coding_bin2int(bin_str[point+1:point+1+std_num])
                        point += std_num
                        if zero_num != 0:
                            zeros = ""
                            for k in range(zero_num):
                                data.append(0)
                                zeros += "0"
        #                    print(f"前零数：{zeros}")
        #                print(f"指针现在在第{point}位(从0开始)")
        #                print(f"解码得出 AC{ac}")
                        data.append(ac)
                        if len(data) == 64:
        #                    print("还没EOB，颜色分量单元内的数据就已经达64个了")
                            break
            return point+1,data

        #函数功能：解Huffman编码之前，先看看是不是RSTn标识。如果是，则直流矫正变量last_DC_Y/Cr/Cb归0(返回0)，指针pointer后调16位。如果不是，忽略。
        def is_RSTn(bin_str,pointer):
            ffdn = ["1111111111010000","1111111111010001","1111111111010010",
                    "1111111111010011","1111111111010100","1111111111010101",
                    "1111111111010110","1111111111010111"]#ffdn
            if bin_str[pointer:pointer+16] in ffdn:
                print("RSTn,直流矫正变量归0")
                return 1
            else:
                return 0
        
        #函数功能：针对YUV420缩减采样模式的JPG图像 压缩数据 进行Huffman解码，执行结束返回 包含图片 所有颜色分量单元 的列表。
        def YUV420_hfm_decoding():#码流：YYYY Cb Cr | YYYY Cb Cr | ...
            merged_bin = element_merge(self.departed_hex_list[10])
            """
            四个像素为： [Y0 U0 V0] [Y1 U1 V1] [Y2 U2 V2] [Y3 U3 V3]
            存放的码流为： Y0 U0 Y1 V1 Y2 U2 Y3 V3
            映射出像素点为：[Y0 U0 V1] [Y1 U0 V1] [Y2 U2 V3] [Y3 U2 V3]
            """
            coding_flow = []
            pointer = 0
            Y_last_DC = 0
            Cr_last_DC = 0
            Cb_last_DC = 0
            count = 0
            pointer_list = [0,0]
            while pointer < len(merged_bin)-32:#原为len(merged_bin):
                """判断一下，如果merged_bin剩下的最后几位，即len(merged_bin)-pointer的这么多位不再构成任何一组最小哈夫曼编码
                即001010 001010 001010 001010 0000 0000共32位，则退出循环。"""
                for a in range(4):
                    if is_RSTn(merged_bin,pointer):
                        Y_last_DC = 0
                        pointer += 16
                        print(f"RSTn,pointer:{pointer}")
                    pointer,mcu = huffman_decoding(merged_bin,self.huffman_table[0],self.huffman_table[1],pointer,Y_last_DC)#Y
                    Y_last_DC = mcu[0]
                    #print(f"MCU:{mcu}")
                    coding_flow.append(mcu)
                    count += 1
                    #print(f"count:{count}，指针在{pointer}位，last_DC{Y_last_DC}。上面是Y")
                    del pointer_list[0]
                    pointer_list.append(pointer)
                    #print(f"{count}:{merged_bin[pointer_list[0]:pointer_list[1]]} pointer:{pointer}")

                if is_RSTn(merged_bin,pointer):
                    Cb_last_DC = 0
                    pointer += 16
                    print(f"RSTn,pointer:{pointer}")
                pointer,mcu = huffman_decoding(merged_bin,self.huffman_table[2],self.huffman_table[3],pointer,Cb_last_DC)#Cr or Cb
                Cb_last_DC = mcu[0]
                #print(f"MCU:{mcu}")
                coding_flow.append(mcu)
                count += 1
                #print(f"count:{count}，指针在{pointer}位，last_DC{Cb_last_DC}。上面是Cb")
                del pointer_list[0]
                pointer_list.append(pointer)
                #print(f"{count}:{merged_bin[pointer_list[0]:pointer_list[1]]} pointer:{pointer}")

                if is_RSTn(merged_bin,pointer):
                    Cr_last_DC = 0
                    pointer += 16
                    print(f"RSTn,pointer:{pointer}")
                pointer,mcu = huffman_decoding(merged_bin,self.huffman_table[2],self.huffman_table[3],pointer,Cr_last_DC)#Cr or Cb
                Cr_last_DC = mcu[0]
                #print(f"MCU:{mcu}")
                coding_flow.append(mcu)
                count += 1
                #print(f"count:{count}，指针在{pointer}位，last_DC{Cr_last_DC}。上面是Cr")
                del pointer_list[0]
                pointer_list.append(pointer)
                #print(f"{count}:{merged_bin[pointer_list[0]:pointer_list[1]]} pointer:{pointer}")

            #print(coding_flow)
            return coding_flow
        self.color_component_unit_flow = YUV420_hfm_decoding()

    #函数功能：反量化及反Z型编码
    def get_iquantumlize_izigzag_res(self):
        #函数功能：定义一个函数，针对YCrCb420方式排列的数据进行反量化。具体排列：YYYY Cb Cr | YYYY Cb Cr | ...
        def dequantumlize(code_lst,qt_label_1,qt_label_2):
            dequantumed_code_flow = []
            pipline = 0
            count = 0
            for i in range(math.floor(len(code_lst))):
                count += 1
                mcu_dequantumed_code_flow = []
                for j in range(64):
                    if (count+1)%6 == 0:
                        mcu_dequantumed_code_flow.append(code_lst[i][j]*qt_label_2[j])
                    elif count%6 == 0:
                        mcu_dequantumed_code_flow.append(code_lst[i][j]*qt_label_2[j])
                    else:
                        mcu_dequantumed_code_flow.append(code_lst[i][j]*qt_label_1[j])
                dequantumed_code_flow.append(mcu_dequantumed_code_flow)
            return dequantumed_code_flow
        #print(dequantumed_code_flow[31])#反量化后的码流
        
        #函数功能：对1个颜色分量单元执行反Z型编码
        def mcu_re_zigzag(mcu):
            ZigZag = [
                    [0, 1, 5, 6, 14, 15, 27, 28],
                    [2, 4, 7, 13, 16, 26, 29, 42],
                    [3, 8, 12, 17, 25, 30, 41, 43],
                    [9, 11, 18, 24, 31, 40, 44, 53],
                    [10, 19, 23, 32, 39, 45, 52, 54],
                    [20, 22, 33, 38, 46, 51, 55, 60],
                    [21, 34, 37, 47, 50, 56, 59, 61],
                    [35, 36, 48, 49, 57, 58, 62, 63]]
            pre_zigzag = [[0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0],
                          [0,0,0,0,0,0,0,0]]
            for i in range(8):
                for j in range(8):
                    pre_zigzag[i][j] = mcu[ZigZag[i][j]]
            return pre_zigzag
        
        #函数功能：对所有颜色分量单元执行反Z型编码
        def total_re_zigzag(dequantumed_code_flow):
            pre_zigzags = []
            for mcu in dequantumed_code_flow:
                pre_zigzags.append(mcu_re_zigzag(mcu))
            return pre_zigzags
        dequantumed_code_flow = dequantumlize(self.color_component_unit_flow,self.quantumlization_table[0],self.quantumlization_table[1])
        self.DCT_list = np.array(total_re_zigzag(dequantumed_code_flow))
    
    #函数功能：获取要隐藏的信息(.txt文件)的gbk汉字编码 的高进制形式数据
    """mod是模式选择：mod=1用于做<高频隐写>时，获取完汉字的高进制编码后，顺便将要隐写位置 对应的量化表位置 上的量化系数改为1，以减小隐写对图片视觉上的影响
                    ；mod=0是默认选项，用于做<量化系数隐写>时，获取汉字的高进制编码。量化表保持原样"""
    def get_higher_base_coding(self,left_shift,filename,num_of_bits,mod=0):#参数mod解释如上
        #函数功能：汉字编码(汉字转二进制字符串)
        def chinese2bin(file_name):#输入.txt文件路径
            with open(file_name,"r",encoding="utf-8") as f:
                message = f.read()
            ans = ''
            for i in message:
                by = bytes(i, encoding='gbk')
                for j in by:
                    jj = bin(int(j))
                    ans += jj[2:]
            return ans
        #函数功能：对二进制编码转2^N进制编码，参数n表示每个2^N进制数字占用的bit数
        def bin_2_2upN_nary(bin_code,N):
            original_bin_len = len(bin_code)#还原的时候，二进制补齐的那末尾几位要舍去，只保留原来位数
            TwoUpN_nary_int_lst = []#用来存二进制转2^n进制结果
            #分两种情况，一种是二进制数字数量刚刚好够转N进制(是N的整数倍)，一种是二进制数字末尾不足以凑成N进制数字了
            if len(bin_code)%N != 0:#二进制数字末尾不足以凑成N进制数字了
                for i in range(N-(len(bin_code)%N)):
                    bin_code += "0"#补齐
            for i in range(round(len(bin_code)/N)):
                choice = bin_code[i*N:i*N+N]
                TwoUpN_nary_int_lst.append(self.std_coding_bin2int(choice))
            return TwoUpN_nary_int_lst
        #函数功能：修改量化表
        def modify_quantumlization_table(choice,tail_len,left_shift,change_into):#choice表示所选择的量化表，可选项为0和1。modified_qt_table是一个含64个整数的列表，即要改成的目标量化表
            dqt_lst = self.departed_hex_list[choice+2]
            #读取量化表，字节5~68 或 5~132，视dqt_precision而定
            for i in range(5,69):
                if i-5 in range(63-tail_len-left_shift,63-left_shift):
                    dqt_lst[i+2] = hex(change_into)
            #获取修改完的量化表
            dqt_label = self.quantumlization_table[choice] = []
            for i in range(5,69):
                dqt_label.append(int(dqt_lst[i],16))
        gbk_code = chinese2bin(filename)
        self.message_bin_code = gbk_code
        self.higher_base_code = bin_2_2upN_nary(gbk_code,num_of_bits)
        tail_len = math.ceil(len(gbk_code)/num_of_bits/(self.height*self.width/16**2)/2)
        if mod == 1:#可选项，做<高频隐写>时开起来，做<量化系数隐写>时关掉，默认关
            modify_quantumlization_table(1,tail_len,left_shift,1)
    
    #函数功能：<迭代器>，考虑到JPG中的YUV420储存顺序：YYYY Cb Cr | YYYY Cb Cr | ...，现定义一个迭代器，参数pip_choise若为0代表Y，1代表Cb，2代表Cr，根据特定分量的上一个索引num，返回下一个索引
    def iterator(self,pip_choice,num):
        if pip_choice == 0:
            if num%6 <= 2:
                return num+1
            elif num%6 == 3:
                return num+3
            else:
                print("迭代器:索引不正确")
        elif pip_choice == 1:
            if num%6 == 4:
                return num+6
            else:
                print("迭代器:索引不正确")
        elif pip_choice == 2:
            if num%6 == 5:
                return num+6
            else:
                print("迭代器:索引不正确")
        else:
            print("迭代器:分量标识不正确")
            
    #函数功能：对图片频域上的颜色数据 进行Z型编码，然后用新的量化表进行量化，
    def get_zigzag_quantumlize_res(self):
        #做Z型编码
        zigzaged_list = []
        ZigZag = [0, 1, 5, 6, 14, 15, 27, 28,
                 2, 4, 7, 13, 16, 26, 29, 42,
                 3, 8, 12, 17, 25, 30, 41, 43,
                 9, 11, 18, 24, 31, 40, 44, 53,
                 10, 19, 23, 32, 39, 45, 52, 54,
                 20, 22, 33, 38, 46, 51, 55, 60,
                 21, 34, 37, 47, 50, 56, 59, 61,
                 35, 36, 48, 49, 57, 58, 62, 63]
        for i in range(len(self.DCT_list)):
            zigzaged_list.append([])
            for j in range(64):
                index = ZigZag.index(j)
                zigzaged_list[-1].append(self.DCT_list[i][index//8][index%8])
        #print(zigzaged_list[:30])
        #做量化
        rccuf = self.requantumlized_color_component_unit_flow
        #print(f"shape of ziazaged_list:{np.shape(zigzaged_list)}")
        for i in range(len(zigzaged_list)):
            rccuf.append([])
            if i%6 <= 3:
                label = 0
            else:
                label = 1
            for j in range(64):
                rccuf[-1].append(round(zigzaged_list[i][j]/self.quantumlization_table[label][j]))
        #修改一下rccuf储存形式，改为[ [Y分量] , [Cb分量] , [Cr分量] ]
        for i in range(len(rccuf)):
            if i%6 <= 3:
                self.reorganized_rccuf[0].append(rccuf[i])
            elif i%6 == 4:
                self.reorganized_rccuf[1].append(rccuf[i])
            else:
                self.reorganized_rccuf[2].append(rccuf[i])
    
    #函数功能：<高频隐写>，将要隐写的信息(汉字)的gbk编码的高进制形式，从图片左到右、上到下，交替写入Cb,Cr颜色分量单元，且高频位置优先写入。
    def write(self,left_shift):
        quanary_code = self.higher_base_code
        tail_len = math.ceil(len(quanary_code)/(self.height*self.width/16**2)/2)
        count = 0
        for i in range(tail_len):
            for j in range(math.floor(self.height*self.width/16**2)):
                if count == len(quanary_code):
                    print(f"i={i},j={j}")
                    break
                self.reorganized_rccuf[1][j][-left_shift-i] = quanary_code[count]
                #print(quanary_code[count])
                count += 1
                if count == len(quanary_code):
                    print(f"i={i},j={j}")
                    break
                self.reorganized_rccuf[2][j][-left_shift-i] = quanary_code[count]
                #print(quanary_code[count])
                count += 1
    
    #函数功能：对1个颜色分量单元进行huffman编码
    def huffman_coding(self,quantumlized_DCT,hfm_table_1,hfm_table_2):
        #函数功能：根据 整数值 确定标准码长度 和 标准码编码
        def std_coding(val):
            code = ""
            position_num = 0
            while 2**position_num-1 < abs(val):
                position_num += 1

            rest_val = abs(val)
            for i in range(position_num):
                position_val = "0"#只能是0或1
                if 2**(position_num-1-i) <= rest_val:
                    position_val = "1"
                    rest_val -= 2**(position_num-1-i)
                else:
                    position_val = "0"
                    rest_val -= 0
                code += position_val
            #进行负数兼容
            neg_code = ""
            if val < 0:
                for i in range(len(code)):
                    if code[i] == "0":
                        neg_code += "1"
                    else:
                        neg_code += "0"
                code = neg_code
            return code,position_num

        #函数功能：输入2位十六进制数和所使用的Huffman表，输出Huffman编码
        def hfm_find(zs,hfm_table):
            for i in range(len(hfm_table)):
                if len(hfm_table[i])==1:
                    continue
                else:
                    for j in range(len(hfm_table[i])-1):
                        if hfm_table[i][j+1][0] == zs:
                            return hfm_table[i][j+1][1]
            print(f"didnt find,zs:{zs}")
            return -1
        init_DC = 0
        #先对Y分量（picture.quantumlized_DCT[0]）用picture.huffman_table[0]进行编码。
        hfm_code = []
        #whether_is_f0 = []
        for i in range(len(quantumlized_DCT)):
            #先选择第i个MCU
            mcu = quantumlized_DCT[i]
            #做一个临时列表，从mcu的后区块(指能形成一单元hfm编码的连续MCU元素组合)往前 储存01字符串编码
            mcu_hfm_code = ""
            #做组分割
            index = []
            whether_is_f0 = []
            count = 0
            for j in range(len(mcu)):
                count += 1
                if mcu[j] != 0 or (j==0 and mcu[0]==0):
                    index.append(j)
                    count = 0
                if count == 16:
                    whether_is_f0.append(j)
                    count = 0
    #        print(f"whether_is_f0{whether_is_f0},index{index}")

            if len(whether_is_f0)!=0:
                while whether_is_f0[-1]>index[-1]:
                    del whether_is_f0[-1]
                    if len(whether_is_f0) == 0:
                        break

            index.extend(whether_is_f0)
            index.sort()
    #        print(f"mixed and sorted index{index}")

            #直流量Huffman编码
            DC_std_code,DC_std_len = std_coding(mcu[0]-init_DC)
            #print(f"MCU[0]:{mcu[0]},init_DC:{init_DC}")
            DC_zero_num = 0
            DC_zero_num_and_std_len = "{:0>2}".format(hex(DC_zero_num).lstrip("0x")+hex(DC_std_len).lstrip("0x"))
            DC_hfm_code = hfm_find(DC_zero_num_and_std_len,hfm_table_1)#str
            mcu_hfm_code += DC_hfm_code+DC_std_code
    #        print(f"DC:zs{DC_zero_num_and_std_len},DC_hfm_code{DC_hfm_code},DC_std_code{DC_std_code},DC_std_val{mcu[0]-init_DC}")
            init_DC = mcu[0]

            #交流量Huffman编码
            for k in range(len(index)-1):
                if index[k+1] in whether_is_f0:#非末尾连续 16个为一组 的0
                    mcu_hfm_code += hfm_find("f0",hfm_table_2)
                else:
                    len_group = index[k+1]-index[k]
                    #if len_group == 16:     
                    AC_zero_num = len_group - 1
                    AC_std_code,AC_std_len = std_coding(mcu[index[k+1]])
                    #把zero_num和std_len组合成一个2位十六进制数
                    AC_zero_num_and_std_len = "{:0>2}".format(hex(AC_zero_num).lstrip("0x")+hex(AC_std_len).lstrip("0x"))
                    AC_hfm_code = hfm_find(AC_zero_num_and_std_len,hfm_table_2)#str
                    #if AC_std_code == "11111111":
                    #    mcu_hfm_code += AC_hfm_code+AC_std_code
                    #else:
                    #    mcu_hfm_code += AC_hfm_code+AC_std_code
                    mcu_hfm_code += AC_hfm_code+AC_std_code
    #                print(f"AC({k}):zs{AC_zero_num_and_std_len},AC_hfm_code{AC_hfm_code},AC_std_code{AC_std_code},AC_std_val{mcu[index[k+1]]}")
            if index[-1] != 63:#index里的元素是mcu中不为0的交流量的索引。若index的最后一元素不为63，说明mcu是以的霍夫曼编码EOB结尾的
                EOB = hfm_find("00",hfm_table_2)
                mcu_hfm_code += EOB
            hfm_code.append(mcu_hfm_code)#把编码结果藏进hfm_code里
    #        print(f"hfm_code[{i}]:{hfm_code[i]}")
        return hfm_code
    
    #函数功能：分别对Y,Cb,Cr三通道的所有颜色分量单元 进行Huffman编码，执行结束返回按照YUV420形式(Y-Y-Y-Y-Cb-Cr)排列的Huffman编码二进制数据字符串
    def get_huffman_coding_res(self):
        huffman_code = []
        huffman_code.append(self.huffman_coding(self.reorganized_rccuf[0],self.huffman_table[0],self.huffman_table[1]))
        huffman_code.append(self.huffman_coding(self.reorganized_rccuf[1],self.huffman_table[2],self.huffman_table[3]))
        huffman_code.append(self.huffman_coding(self.reorganized_rccuf[2],self.huffman_table[2],self.huffman_table[3]))
        #以下代码用于按照YUV420的格式（参照微信传输非原图时用的格式）来组织YCbCr三通道数据于self.huffman_code_flow
        #具体为：YYYY Cb Cr | YYYY Cb Cr | ...
        for i in range(round((len(huffman_code[0])+len(huffman_code[1])+len(huffman_code[2]))/6)):
            self.huffman_code_flow.append(huffman_code[0][i*4+0])
            self.huffman_code_flow.append(huffman_code[0][i*4+1])
            self.huffman_code_flow.append(huffman_code[0][i*4+2])
            self.huffman_code_flow.append(huffman_code[0][i*4+3])
            self.huffman_code_flow.append(huffman_code[1][i])
            self.huffman_code_flow.append(huffman_code[2][i])
        merged_str = ""
        for i in range(len(self.huffman_code_flow)):
            merged_str += self.huffman_code_flow[i]
        self.huffman_code_flow = merged_str#修改这个变量的类型
        
    #函数功能：将隐写完成后的此张JPG所有数据做成bytes类型数据，并写入.jpg格式文件
    def generate_JPG(self,output_filename):
        def bin_list2int_list(bin_lst):
            int_lst = []
            for i in range(len(bin_lst)):
                num = int(bin_lst[i],2)
                int_lst.append(num)
            return int_lst
        def hex_list2int_list(hex_lst):
            int_lst = []
            for i in range(len(hex_lst)):
                num = int(hex_lst[i],16)
                int_lst.append(num)
            return int_lst
        #先将所有数据转成int类型
        JPG_int = []
        for i in range(12):
            if i == 10:
                """if len(self.huffman_code_flow)%8!=0:
                    for f in range(8-len(self.huffman_code_flow)%8):
                        self.huffman_code_flow += "0" """
                for f in range(32):
                        self.huffman_code_flow += "0"
                #要先把self.total_huffman_code里面的数据转为8个一组
                departed_hex_list_10 = []
                for j in range(math.floor(len(self.huffman_code_flow)/8 - 1)):
                    departed_hex_list_10.append(self.huffman_code_flow[j*8:j*8+8])
                #再进行类型转换
                JPG_int.append(bin_list2int_list(departed_hex_list_10))
                #在JPG_int[10]中所有255元素后面添加一个000元素
                length = len(JPG_int[10])
                for j in range(len(JPG_int[10])):
                    if JPG_int[10][length-1-j] == 255:
                        #print(f"执行ff后加00，次数{j}")
                        JPG_int[10].insert((length-1-j)+1,0)
            else:
                JPG_int.append(hex_list2int_list(self.departed_hex_list[i]))
        JPG_int_reorganize = []
        for i in range(len(JPG_int)):
            JPG_int_reorganize.extend(JPG_int[i])
        JPG_bytes = bytes(JPG_int_reorganize)
        #下面直接写入文件
        # 打开文件，指定模式为二进制写入模式
        with open(output_filename, 'wb') as file:#'D:/Steganography/out_put_writeCb.bin'
            # 将字节对象写入文件
            file.write(JPG_bytes)
            
    #函数功能：从图片的所有颜色分量单元中解码出 隐藏信息。
    def read(self):
        tail_len = 1
        left_shift = 0
        for i in range(64):
            if self.quantumlization_table[1][-i-1] == 1:
                left_shift = i
                break
        for i in range(64-left_shift-1):
            if self.quantumlization_table[1][-i-1-left_shift-1] == 1:
                tail_len += 1
            else:
                break
        #修改一下ccuf储存形式，改为[ [Y分量] , [Cb分量] , [Cr分量] ],存在self.reorganized_ccuf中
        ccuf = self.color_component_unit_flow 
        for i in range(len(ccuf)):
            if i%6 <= 3:
                self.reorganized_ccuf[0].append(ccuf[i])
            elif i%6 == 4:
                self.reorganized_ccuf[1].append(ccuf[i])
            else:
                self.reorganized_ccuf[2].append(ccuf[i])           
        quanery_code = self.higher_base_code
        for i in range(tail_len):
            for j in range(math.floor(self.height*self.width/16**2)):
                quanery_code.append(self.reorganized_ccuf[1][j][-1-left_shift-i])
                if quanery_code[-1] == 0:
                    break
                quanery_code.append(self.reorganized_ccuf[2][j][-1-left_shift-i])
                if quanery_code[-1] == 0:
                    break
        #高进制转二进制
        code0 = self.std_coding_int2bin(self.higher_base_code[0])#首先要知道高进制是几进制
        num_of_bits = len(code0)#是num_of_bits进制
        
        #函数功能：2^N进制转二进制
        def _2upN_nary2bin(TwoUpN_nary_int_lst,N,original_bin_len):#TwoUpN_nary_int_lst是由2^N进制数字组成的列表，N表示2^N进制，original_bin_len是二进制数原本的长度
            bin_code = ""
            for i in range(len(TwoUpN_nary_int_lst)):
                bin_code += self.std_coding_int2bin(TwoUpN_nary_int_lst[i])
            bin_code = bin_code[:original_bin_len]
            return bin_code
        #函数功能：汉字解码(二进制字符串转汉字)函数    
        def bin2chinese(bin_code):#输入gbk编码（一种汉字编码）
            ans = ''
            for i in range(0, len(bin_code), 16):
                #print(f"count:{i}")
                    a = bin_code[i:i + 8]
                    b = bin_code[i + 8:i + 16]
                    try:
                        a = int(a, 2)
                        b = int(b, 2)
                    except ValueError:
                        break
                    ch = struct.pack("<B", a) + struct.pack("<B", b)
                    ans += str(ch, encoding='gbk')
            return ans
        bin_code = _2upN_nary2bin(self.higher_base_code,num_of_bits,num_of_bits*len(self.higher_base_code))
        self.message = bin2chinese(bin_code)
        
    #函数功能：将要隐写的信息 交替隐写在图片的两张量化表上，高频优先。本质是修改量化表内的量化系数
    def qt_write(self):
        max_bin_qt_writing_len = sum(self.qt_position[0]) + sum(self.qt_position[1])
        if max_bin_qt_writing_len >= len(self.message_bin_code):
            #从量化表高频位置到低频位置，交替着读取要写入的位数。
            qt_position_for_message = []#用于分割self.message_bin_code的指导列表
            accumulate_qpfm = []#上面列表的 累积 版本
            for i in range(125):
                qt_position_for_message.append(self.qt_position[i%2][-2-(i//2)])
            accumulate_val = 0
            for i in range(125):
                accumulate_val += qt_position_for_message[i]
                accumulate_qpfm.append(accumulate_val)
            self.qt_departed_message_bin_code.append(self.message_bin_code[:accumulate_qpfm[0]])
            for i in range(124):  
                if self.message_bin_code[accumulate_qpfm[i]:accumulate_qpfm[i+1]] == "":
                    break
                self.qt_departed_message_bin_code.append(self.message_bin_code[accumulate_qpfm[i]:accumulate_qpfm[i+1]])
            #self.qt_departed_message_bin_code.append(self.message_bin_code[accumulate_qpfm[-1]:])
            #从量化表高频位置到低频位置，交替着在量化表1和表2上写入。
        else:
            print(f"最多只能在量化表中写入{max_bin_qt_writing_len//16}个汉字")
            return -1
        #接下来写入量化表
        for i in range(len(self.qt_departed_message_bin_code)):
            self.quantumlization_table[i%2][-2-(i//2)] = int(self.qt_departed_message_bin_code[i],2)+1 #记得改成int类型。从量化表1的倒2个元素开始写。全部加1，防止量化表出现0
        self.quantumlization_table[0][-1] = len(self.message_bin_code)//16#从量化表1的倒1个元素储存汉字数量
        #把self.departed_hex_list[2],self.departed_hex_list[3]里代表量化表的数据也改了
        for i in range(5,69):
            self.departed_hex_list[2][i] = hex(self.quantumlization_table[0][i-5])
            self.departed_hex_list[3][i] = hex(self.quantumlization_table[1][i-5])
            
    #self.higher_base_code = []
    #self.message_bin_code = ""
    #函数功能：从图片的两张量化表中读取隐藏信息，并储存于self.message
    def qt_read(self):
        qt_val_list = []
        qt_position_list = []
        for i in range(125):
            qt_val_list.append(self.quantumlization_table[i%2][-2-(i//2)]-1)
            qt_position_list.append(self.qt_position[i%2][-2-(i//2)])
        #print(f"qt_val_list:{qt_val_list}")
        for i in range(125):
            bin_val = "{:0>10}".format(bin(qt_val_list[i]).lstrip("0b"))
            bits_num = qt_position_list[i]
            #print(f"bits_num:{bits_num},bin_val:{bin_val[-bits_num:]}")
            self.message_bin_code += bin_val[-bits_num:]
            #print(f"i+1={i+1}:bin_val:{bin_val[-bits_num:]}")
        #self.message_bin_code长度只允许是 16 的整数倍数
        len_should_be = self.quantumlization_table[0][-1]*16
        len_real = 0
        for i in range(125):
            len_real += qt_position_list[i]
            if len_real > len_should_be:
                len_diff = len_should_be - (len_real - qt_position_list[i])
                remain_bits = self.message_bin_code[len_real-len_diff:len_real]
                self.message_bin_code = self.message_bin_code[:len_should_be-len_diff]+remain_bits
                break
            elif len_real == len_should_be:
                self.message_bin_code = self.message_bin_code[:len_should_be]
                break
            #print(self.message_bin_code)
        #接下来尝试把self.message_bin_code译码成汉字
        #函数功能：汉字解码(二进制字符串转汉字)函数    
        def bin2chinese(bin_code):#输入gbk编码（一种汉字编码）
            ans = ''
            try:
                for i in range(0, len(bin_code), 16):
                    #print(f"count:{i}")
                    a = bin_code[i:i + 8]
                    b = bin_code[i + 8:i + 16]
                    a = int(a, 2)
                    b = int(b, 2)
                    ch = struct.pack("<B", a) + struct.pack("<B", b)
                    #print(ch,str(ch, encoding='gbk'))
                    ans += str(ch, encoding='gbk')  
            except UnicodeDecodeError:
                return ans
            return ans        
        self.message = bin2chinese(self.message_bin_code)
    
    #功能函数：读取一张任意格式图片的RGB数据
    def read_RGB(self):
        from PIL import Image
        import numpy as np
        import math
        img = Image.open(self.file_path) #读取图片存入变量img中
        print(img.format) #输出图片格式(str)
        print(img.size) #输出图片大小信息 （宽度w，高度h）tuple = (int,int)
        #像素载入
        pix = img.load()
        width = img.size[0] #.size 方法返回的是一个元组 tuple =(int,int) 
        height = img.size[1] 
        #获取像素点的RGB值
        image_r = [] #创建3个数组存储RGB值
        image_g = []
        image_b = []
        for y in range(height):#遍历每一个像素点，将图像看作是一个二维数组，
            image_r.append([])
            image_g.append([])
            image_b.append([])
            for x in range(width): #如果x循环在外层输出的图像会发生一个九十度的翻转
                r,g,b =pix[x,y] #此处的r,g,b是像素点pix[x,y]的RGB值
                image_r[y].append(r)
                image_g[y].append(g)
                image_b[y].append(b)
        self.img_r = image_r
        self.img_g = image_g
        self.img_b = image_b
        self.width = math.ceil(width/16)*16
        self.height = math.ceil(height/16)*16
        if self.width != width:
            for i in range(self.width-width):
                self.img_r[i].append(0)
                self.img_g[i].append(0)
                self.img_b[i].append(0)
        if self.height != height:
            #print("RUN!")
            for i in range(self.height-height):
                #print(f"complement:{i}")
                self.img_r = np.append(self.img_r,np.array([[0]*self.width]),axis=0)
                self.img_g = np.append(self.img_g,np.array([[0]*self.width]),axis=0)
                self.img_b = np.append(self.img_b,np.array([[0]*self.width]),axis=0)
        #print(self.img_r)
        #print(f"len_r:{len(self.img_r)}")
        self.img_Y = 0.299*self.img_r+0.587*self.img_g+0.114*self.img_b#定义域对称 -128~128
        self.img_Cb = 0.564*(self.img_b-self.img_Y)
        self.img_Cr = 0.713*(self.img_r-self.img_Y)
        self.img_Y -= 128
        
    def down_sampling(self): 
        """
        YUV4:4:4 row_step=1,column_step=1
            ini_row_Cr = 0,ini_column_Cr = 0
            ini_row_Cb = 0,ini_column_Cb = 0
        YUV4:2:2 row_step=1,column_step=2
            ini_row_Cr = 0,ini_column_Cr = 0
            ini_row_Cb = 0,ini_column_Cb = 1
        YUV4:1:1 row_step=1,column_step=4
            ini_row_Cr = 0,ini_column_Cr = 0
            ini_row_Cb = 0,ini_column_Cb = 2
        YUV4:2:0 row_step=2,column_step=2
            ini_row_Cr = 0,ini_column_Cr = 0
            ini_row_Cb = 1,ini_column_Cb = 2
        Y—Y,U—Cr,V—Cb
        """
        #YUV4:2:0
        row_step = 2 #全取样1，隔行取样2
        column_step = 2 #全取样1，隔点取样2
        #根据 步长和各通道size确定 缩减取样后的通道的size
        reduced_Cb = np.zeros((math.ceil(self.height/row_step),math.ceil(self.width/column_step)))
        reduced_Cr = np.zeros((math.ceil(self.height/row_step),math.ceil(self.width/column_step)))
        #print(reduced_Cb)
        point_row_Cr=ini_row_Cr = 0
        point_column_Cr=ini_column_Cr = 0
        point_row_Cb=ini_row_Cb = 0
        point_column_Cb=ini_column_Cb = 0
        
        while point_row_Cr<self.height:
            point_column_Cr = ini_column_Cr
            while point_column_Cr<self.width:
                ans = (self.img_Cr[point_row_Cr][point_column_Cr]+self.img_Cr[point_row_Cr+1][point_column_Cr]+self.img_Cr[point_row_Cr][point_column_Cr+1]+self.img_Cr[point_row_Cr+1][point_column_Cr+1])/4
                '''
                if ans >= 0:
                    reduced_Cr[int((point_row_Cr-ini_row_Cr)/row_step)][int((point_column_Cr-ini_column_Cr)/column_step)] = np.ceil(ans)
                if ans < 0:
                    reduced_Cr[int((point_row_Cr-ini_row_Cr)/row_step)][int((point_column_Cr-ini_column_Cr)/column_step)] = np.floor(ans)
                '''
                reduced_Cr[int((point_row_Cr-ini_row_Cr)/row_step)][int((point_column_Cr-ini_column_Cr)/column_step)] = round(ans)
                point_column_Cr += column_step
            point_row_Cr += row_step
        
        while point_row_Cb<self.height:
            point_column_Cb = ini_column_Cb
            while point_column_Cb<self.width:
                ans = (self.img_Cb[point_row_Cb][point_column_Cb]+self.img_Cb[point_row_Cb+1][point_column_Cb]+self.img_Cb[point_row_Cb][point_column_Cb+1]+self.img_Cb[point_row_Cb+1][point_column_Cb+1])/4
                '''
                if ans >= 0:
                    reduced_Cb[int((point_row_Cb-ini_row_Cb)/row_step)][int((point_column_Cb-ini_column_Cb)/column_step)] = np.ceil(ans)
                if ans < 0:
                    reduced_Cb[int((point_row_Cb-ini_row_Cb)/row_step)][int((point_column_Cb-ini_column_Cb)/column_step)] = np.floor(ans)
                '''
                reduced_Cb[int((point_row_Cb-ini_row_Cb)/row_step)][int((point_column_Cb-ini_column_Cb)/column_step)] = round(ans)
                point_column_Cb += column_step
            point_row_Cb += row_step
        self.reduced_Cr = reduced_Cr
        self.reduced_Cb = reduced_Cb

    #算DCT用此函数，此函数计算部分直接调用scipy库的dctn()来算二维dct
    def DCT_scipy(self,block_hei,block_wid):#block_wid,block_hei为每次进行离散余弦变换区域的宽和高
        from scipy.fftpack import dctn
        #初始化Cr_DCT和Cb_DCT
        wid_reduced_Cr = int(np.size(self.reduced_Cr[0]))
        hei_reduced_Cr = int(int(np.size(self.reduced_Cr))/int(np.size(self.reduced_Cr[0])))
        #self.Cr_DCT = np.zeros((hei_reduced_Cr,wid_reduced_Cr))
        wid_reduced_Cb = int(np.size(self.reduced_Cb[0]))
        hei_reduced_Cb = int(int(np.size(self.reduced_Cb))/int(np.size(self.reduced_Cb[0])))
        #self.Cb_DCT = np.zeros((hei_reduced_Cb,wid_reduced_Cb))
        #先针对亮度Y进行 block_wid*block_hei 的DCT
        #先数一数block为单位，此图像有row*column个block，其中row与column都要向下取整
        
        def DCT_one_pipline_scipy(pip,pip_DCT):
            row = math.floor(int(np.size(pip)/np.size(pip[0]))/block_hei)
            column = math.floor(int(np.size(pip[0]))/block_wid)
            #print(f"row{row},column{column},column*block_wid{column*block_wid}")
            #print(pip)
            p=0
            for i_row in range(row):
                for i_column in range(column):
                    p+=1
                    #print(f"count:{p}")
                    i_hei = i_row*block_hei
                    i_wid = i_column*block_wid
                    block = pip[i_hei:i_hei+block_hei,i_wid:i_wid+block_wid]
                    dct_scipy = dctn(block,type=2, norm='ortho')
                    for m in range(len(dct_scipy[0])):
                        for n in range(len(dct_scipy)):
                            dct_scipy[m][n] = round(dct_scipy[m][n])
                    #print(dct_scipy)
                    pip_DCT.append(dct_scipy)
        DCT_one_pipline_scipy(self.img_Y,self.Y_DCT)
        DCT_one_pipline_scipy(self.reduced_Cb,self.Cb_DCT)
        DCT_one_pipline_scipy(self.reduced_Cr,self.Cr_DCT)
        
        count_DCT = [0,0,0]
        #print(len(self.Y_DCT),len(self.Cb_DCT),len(self.Cr_DCT))
        #print(len(self.Y_DCT)+len(self.Cb_DCT)+len(self.Cr_DCT))
        #print(self.Y_DCT[0])
        #print(len(self.Y_DCT))
        row_cube_num = int(self.width/block_wid)
        for i in range(len(self.Y_DCT)+len(self.Cb_DCT)+len(self.Cr_DCT)):
            if i%6 == 0:
                #print(count_DCT[0])
                self.DCT_list.append(self.Y_DCT[count_DCT[0]])
                self.DCT_list.append(self.Y_DCT[count_DCT[0]+1])
                self.DCT_list.append(self.Y_DCT[count_DCT[0]+row_cube_num])
                self.DCT_list.append(self.Y_DCT[count_DCT[0]+1+row_cube_num])
                count_DCT[0] += 2
                if count_DCT[0]%row_cube_num == 0:
                    count_DCT[0] += row_cube_num
            elif i%6 == 4:
                #print(count_DCT[1])
                self.DCT_list.append(self.Cb_DCT[count_DCT[1]])
                count_DCT[1]+=1
            elif i%6 == 5:
                #print(count_DCT[2])
                self.DCT_list.append(self.Cr_DCT[count_DCT[2]])
                count_DCT[2]+=1
        self.DCT_list = np.array(self.DCT_list)
           
    def DCT2steganography(self,left_shift,tail_len):
        #做Z型编码
        zigzaged_list = []
        ZigZag = [0, 1, 5, 6, 14, 15, 27, 28,
                 2, 4, 7, 13, 16, 26, 29, 42,
                 3, 8, 12, 17, 25, 30, 41, 43,
                 9, 11, 18, 24, 31, 40, 44, 53,
                 10, 19, 23, 32, 39, 45, 52, 54,
                 20, 22, 33, 38, 46, 51, 55, 60,
                 21, 34, 37, 47, 50, 56, 59, 61,
                 35, 36, 48, 49, 57, 58, 62, 63]
        for i in range(len(self.DCT_list)):
            zigzaged_list.append([])
            for j in range(64):
                index = ZigZag.index(j)
                zigzaged_list[-1].append(self.DCT_list[i][index//8][index%8])
        #接下来将数据储存为[[Y],[Cb],[Cr]]三通道
        for i in range(len(zigzaged_list)):
            if i%6 <= 3:
                self.reorganized_rccuf[0].append(zigzaged_list[i])
            elif i%6 == 4:
                self.reorganized_rccuf[1].append(zigzaged_list[i])
            else:
                self.reorganized_rccuf[2].append(zigzaged_list[i])
        #将数据按照一Cb一Cr地从高频往低频读取
        quanery_code = self.higher_base_code
        '''这个tail_len目前无从得知。我们目前假定tail_len和left_shift都是提前告知的，手动给定。
        要全自动的话需要使用统计方法，判断这两者的值。麻烦暂且不搞'''
        tail_len = 59#直接开大一点
        for i in range(tail_len):
            for j in range(math.floor(self.height*self.width/16**2)):
                quanery_code.append(self.reorganized_rccuf[1][j][-left_shift-i])
                #if quanery_code[-1] == 0:
                 #   break
                quanery_code.append(self.reorganized_rccuf[2][j][-left_shift-i])
                #if quanery_code[-1] == 0:
                 #   break
        #到这里相当于已经完成了self.higher_base_code的读取，但这时候还是模糊数据，需要根据模糊区间将其转为标准隐写数字点，such as 只含{-3,-2,0,2,3}的数据
        #quanery_code需要剔除一些非隐写位置。只保留隐写位置。如何识别这一点呢？
                '''if len(quanery_code)>51:
                    sorted_q2 = sorted(quanery_code[-25:])
                    #quanery_code[-26]
                    sorted_q1 = sorted(quanery_code[-51:-26])
                    if sorted_q2[3]>0 and sorted_q1[3]>0:
                        min_val = min(quanery_code[-51:])
                        idx = quanery_code[-51:].index(min_val)
                        for k in range(51-1-idx+26):
                            quanery_code.pop()
                    return 0'''
        
    #功能函数，把-1和1映射到-vaguer和vaguer
    def vagulize(self,vaguer,num_of_bits=1):#num_of_bits目前只是摆设。
        for i in range(len(self.higher_base_code)):
            if self.higher_base_code[i] == 1:
                self.higher_base_code[i] = vaguer
            elif self.higher_base_code[i] == -1:
                self.higher_base_code[i] = -vaguer
        self.higher_base_code.extend([vaguer]*25)#插入50位全正序列代表结束
        self.higher_base_code.append(-vaguer*3)#很大的负数
        self.higher_base_code.extend([vaguer]*25)
                
    def ivaguer(self,num_of_bits=1):
        for i in range(len(self.higher_base_code)):
            if self.higher_base_code[i] > 0:
                self.higher_base_code[i] = 1
            elif self.higher_base_code[i] < 0:
                self.higher_base_code[i] = -1
                
    def read_from_HBC(self,num_of_bits=1):
        #函数功能：2^N进制转二进制
        def _2upN_nary2bin(TwoUpN_nary_int_lst,N,original_bin_len):#TwoUpN_nary_int_lst是由2^N进制数字组成的列表，N表示2^N进制，original_bin_len是二进制数原本的长度
            bin_code = ""
            for i in range(len(TwoUpN_nary_int_lst)):
                bin_code += self.std_coding_int2bin(TwoUpN_nary_int_lst[i])
            bin_code = bin_code[:original_bin_len]
            return bin_code
        #函数功能：汉字解码(二进制字符串转汉字)函数    
        def bin2chinese(bin_code):#输入gbk编码（一种汉字编码）
            ans = ''
            i = 0
            while i <= len(bin_code):
                #print(f"count:{i}")
                a = bin_code[i:i + 8]
                b = bin_code[i + 8:i + 16]
                try:
                    a = int(a, 2)
                    b = int(b, 2)
                except ValueError:
                    break
                try:
                    ch = struct.pack("<B", a) + struct.pack("<B", b)
                    ans += str(ch, encoding='gbk')
                except UnicodeDecodeError:
                    ans += "0"
                    i += 1
                    continue
                i+=16
            return ans
        bin_code = _2upN_nary2bin(self.higher_base_code,num_of_bits,num_of_bits*len(self.higher_base_code))
        self.message = bin2chinese(bin_code)
    
    #核心！一键执行<JPG色度通道高频 隐写>
    def total_writing_process(self,left_shift,qt_change_into,filename,num_of_bits,output_filename):
        self.init_necessary_infomation()#读取P.jpg二进制数据，从数据中读取必要信息
        self.get_huffman_decoding_res()#根据必要信息中的哈夫曼表解码压缩数据得到MCU(最小编码单元)
        self.get_iquantumlize_izigzag_res()#反Z型编码。根据量化表进行反量化，得离散余弦矩阵
        """
        self.get_higher_base_coding()解释：
        1.将filename.txt进行汉字编码，编码的进制数由num_of_bits决定(如:为3代表8进制。但为1就已绰绰有余)，是隐写容量与图片质量的取舍。
        2.参数mod=1,表示开启 修改量化表：将CbCr分量单元中要写入的位置对应的量化系数改小，大大减小隐写对图片的视觉影响
        """
        self.get_higher_base_coding(left_shift,filename,num_of_bits,1)#注释如上
        self.get_zigzag_quantumlize_res()#Z型编码，用新量化表量化离散余弦矩阵得MCU
        self.write(left_shift)#把隐藏信息写入各MCU(最小编码单元)中的CbCr分量单元
        self.get_huffman_coding_res()#对隐写后的各MCU进行霍夫曼编码
        self.generate_JPG(output_filename)#按照JPG结构组织数据，并将其写入SP.jpg
        
    #核心！一键执行<JPG色度通道高频 解隐写>
    def total_reading_process(self):
        self.init_necessary_infomation()#读取P.jpg二进制数据，从数据中读取必要信息
        self.get_huffman_decoding_res()#根据必要信息中的哈夫曼表解码压缩数据得到MCU(最小编码单元)
        self.read()#从各MCU的颜色CbCr分量单元中读取隐写信息
        print(self.message)#打印出隐写信息
        
    #核心！一键执行<JPG量化系数 隐写>
    def qt_writing_process(self,filename,output_filename):
        self.init_necessary_infomation()#读取P.jpg二进制数据，从数据中读取必要信息
        self.get_huffman_decoding_res()#根据必要信息中的哈夫曼表解码压缩数据得到MCU(最小编码单元)
        self.get_iquantumlize_izigzag_res()#反Z型编码。根据量化表进行反量化，得离散余弦矩阵
        self.get_higher_base_coding(0,filename,num_of_bits=1)#获取filename文件内汉字的2^num_of_bits进制编码
        self.qt_write()#在量化表中写入数据
        self.get_zigzag_quantumlize_res()#Z型编码，用新量化表量化离散余弦矩阵得MCU
        self.get_huffman_coding_res()#对隐写后的各MCU进行霍夫曼编码
        self.generate_JPG(output_filename)#按照JPG结构组织数据，并将其写入SP.jpg
    
    #核心！一键执行<JPG量化系数 解隐写>
    def qt_reading_process(self):
        self.init_necessary_infomation()#读取P.jpg二进制数据，从数据中读取必要信息,特别是量化表
        self.qt_read()#从量化表中读出汉字编码，并译出汉字
        print(self.message)#打印出隐写信息
        
    #第三题，一键执行<JPG色度通道高频 模糊隐写>
    def hf_vague_writing_process(self,left_shift,qt_change_into,filename,num_of_bits,output_filename):#!!!这里num_of_bits暂时只能等于1
        self.init_necessary_infomation()#读取P.jpg二进制数据，从数据中读取必要信息
        self.get_huffman_decoding_res()#根据必要信息中的哈夫曼表解码压缩数据得到MCU(最小编码单元)
        self.get_iquantumlize_izigzag_res()#反Z型编码。根据量化表进行反量化，得离散余弦矩阵
        """
        self.get_higher_base_coding()解释：
        1.将filename.txt进行汉字编码，编码的进制数由num_of_bits决定(如:为3代表8进制。但为1就已绰绰有余)，是隐写容量与图片质量的取舍。
        2.参数mod=1,表示开启 修改量化表：将CbCr分量单元中要写入的位置对应的量化系数改小，大大减小隐写对图片的视觉影响
        """
        self.get_higher_base_coding(left_shift,filename,num_of_bits,1)#注释如上
        self.get_zigzag_quantumlize_res()#Z型编码，用新量化表量化离散余弦矩阵得MCU
        vaguer = 10#就是把1和-1映射到5和-5
        #在此步需要一个模糊映射，将self.higher_base_code转为【模糊的】【都用正负5取代1和0就好啦，适应num_of_bits只能选1】
        self.vagulize(vaguer)#可选参数num_of_bits
        self.write(left_shift)#把隐藏信息写入各MCU(最小编码单元)中的CbCr分量单元
        self.get_huffman_coding_res()#对隐写后的各MCU进行霍夫曼编码
        self.generate_JPG(output_filename)#按照JPG结构组织数据，并将其写入SP.jpg
    
    #核心！一键执行<视觉读取>【先让它适应1bit就好啦！】
    def hf_vague_reading_process(self,left_shift,tail_len,num_of_bits):#！！！目前num_of_bits暂时只能等于1
        self.read_RGB()#先读取self.file_name的RGB数据，并转为YCbCr
        self.down_sampling()#对YCbCr数据进行缩减采样
        self.DCT_scipy(8,8)#使用scipy里对应的ndct()函数对YCbCr数据进行DCT变换
        #需要将DCT中读出的数据转为 按照隐写的顺序排序cb-3/cr-3/cb-3/cr-3
        self.DCT2steganography(left_shift,tail_len)#left_shift肯定是3，tail_len不知道。波动的higher_base_code有了
        #tail_len????
        self.ivaguer()#作用于self.higher_base_code，负的转-1，正的转1
        self.read_from_HBC()
        print(self.message)


# In[4]:


#第一题 法1
#执行<JPG色度通道高频 隐写>

P_1_HF = Picture('D:/Steganography/P.jpg')#用 待隐写的原图P.jpg 创建实例
left_shift = 3 #从Cb,Cr颜色分量单元的倒数第left_shift位开始隐写。
num_of_bits = 1 #汉字编码的进制数，表示2^num_of_bits进制。是隐写最大容量 与 图片质量 的取舍。如:num_of_bits=3，则相比num_of_bits=1,隐写容量扩大8倍。
qt_change_into = 1#更改量化表上与 颜色分量单元中要隐写的位置对应的 量化系数。此值越小，隐写对图片的影响就越小，必须为整数，最小值为1，最大值为2^8
txt_1 = "D:/Steganography/深圳杯数学建模挑战赛.txt"#要隐写的内容的文件位置
output_1_HF = f'D:/Steganography/SP_1.jpg'#隐写后图片的导出位置
P_1_HF.total_writing_process(left_shift,qt_change_into,txt_1,num_of_bits,output_1_HF)#执行隐写


# In[ ]:


#第一题 法1
#执行<JPG色度通道高频 解隐写>

SP_1_HF = Picture('D:/Steganography/SP_1.jpg')#用 含隐写信息的图片SP_1_HF.jpg 创建实例
SP_1_HF.total_reading_process()#执行解隐写 并 print 


# In[ ]:


#第一题 法2
#执行<JPG量化系数 隐写>

P_1_QT = Picture('D:/Steganography/P.jpg')#用 待隐写的原图P.jpg 创建实例
txt_1 = "D:/Steganography/深圳杯数学建模挑战赛.txt"#要隐写的内容的文件位置
output_1_QT = f'D:/Steganography/SP_1_QT.jpg'#隐写后图片的导出位置
P_1_QT.qt_writing_process(txt_1,output_1_QT)#执行隐写


# In[ ]:


#第一题 法2
#执行<JPG量化系数 解隐写>

SP_1_QT = Picture('D:/Steganography/SP_1_QT.jpg')#用 含隐写信息的图片SP_1_QT.jpg 创建实例
SP_1_QT.qt_reading_process()#执行解隐写 并 print


# In[ ]:


#第二题
#执行<JPG色度通道高频 隐写>

P_2_HF = Picture('D:/Steganography/P.jpg')#用 待隐写的原图P.jpg 创建实例
left_shift = 3 #从Cb,Cr颜色分量单元的倒数第left_shift位开始隐写。
num_of_bits = 3 #汉字编码的进制数，表示2^num_of_bits进制。是隐写最大容量 与 图片质量 的取舍。
                #如:num_of_bits=3，则容量扩大8倍。但其实写入整个《著作权法》，num_of_bits=1就已绰绰有余，且图像质量损失极小。
txt_2 = "D:/Steganography/中华人民共和国著作权法第三次修正案.txt"
qt_change_into = 1#更改量化表上与 颜色分量单元中要隐写的位置对应的 量化系数。此值越小，隐写对图片的影响就越小
#执行隐写：将 中华人民共和国著作权法第三次修正案.txt 写入P.jpg 并导出为SP_2.jpg
output_2 = f'D:/Steganography/SP_2_HF_18本_隐写内容用8进制GBK编码.jpg'#隐写后图片的导出位置
P_2_HF.total_writing_process(left_shift,qt_change_into,txt_2,num_of_bits,output_2)#执行隐写


# In[ ]:


#第二题
#执行<JPG色度通道高频 解隐写>

SP_2_HF = Picture('D:/Steganography/SP_2_HF_18本_隐写内容用8进制GBK编码.jpg')#用 含隐写信息的图片SP_2_HF.jpg 创建实例
SP_2_HF.total_reading_process()#执行解隐写 并 print


# In[ ]:


#第三题
#执行<JPG量化系数 隐写>

P_3_QT = Picture('D:/Steganography/P.jpg')#用 待隐写的原图P.jpg 创建实例
txt_1 = "D:/Steganography/深圳杯数学建模挑战赛.txt"#要隐写的信息的文件位置
output_3 = f'D:/Steganography/SP_3_QT.jpg'#隐写后图片的导出位置
P_3_QT.qt_writing_process(txt_1,output_3)#执行隐写


# In[ ]:


#第三题
#执行<JPG量化系数 解隐写>

SP_3_QT = Picture('D:/Steganography/SP_3_QT.jpg')#用 含隐写信息的图片SP_3_QT.jpg 创建实例
SP_3_QT.qt_reading_process()#执行解隐写 并 print

#滤镜处理后再解隐写
#SP_3_QT = Picture('D:/Steganography/SP_3_QT_filter.jpg')#用 含隐写信息的图片SP_3_QT.jpg 创建实例
#SP_3_QT.qt_reading_process()#执行解隐写 并 print


# In[ ]:


#模糊隐写
P_3_vague_HF = Picture('D:/Steganography/P.jpg')
left_shift = 3 #从Cb,Cr颜色分量单元的倒数第left_shift位开始隐写。
num_of_bits = 1 #!!!暂时只能=1。汉字编码的进制数，表示2^num_of_bits进制。是隐写最大容量 与 图片质量 的取舍。
                #如:num_of_bits=3，则容量扩大8倍。但其实写入整个《著作权法》，num_of_bits=1就已绰绰有余，且图像质量损失极小。
txt_4 = "D:/Steganography/中华人民共和国著作权法第三次修正案.txt"
qt_change_into = 1#更改量化表上与 颜色分量单元中要隐写的位置对应的 量化系数。此值越小，隐写对图片的影响就越小
#执行隐写：将 中华人民共和国著作权法第三次修正案.txt 写入P.jpg 并导出为SP_2.jpg
output_4 = f'D:/Steganography/SP_3_vague_HF_1本_隐写内容用2进制GBK编码.jpg'#隐写后图片的导出位置
P_3_vague_HF.hf_vague_writing_process(left_shift,qt_change_into,txt_4,1,output_4)


# In[4]:


#视觉读取
SP_3_vague_HF = Picture('D:/Steganography/SP_3_vague_HF_1本_隐写内容用2进制GBK编码.jpg')
left_shift = 3
tail_len = 60
num_of_bits = 1#暂时只能＝1
SP_3_vague_HF.hf_vague_reading_process(left_shift,tail_len,num_of_bits)


# In[ ]:




