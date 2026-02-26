# PyStart Linux 打包脚本

本目录包含用于在Linux系统上构建PyStart软件包的脚本。

## 文件说明

- `build_common.sh` - 共享的构建函数，被其他脚本调用
- `build_deb.sh` - 用于构建Debian/Ubuntu系统的.deb软件包
- `build_rpm.sh` - 用于构建Fedora/RHEL/CentOS系统的.rpm软件包
- `PyStart.desktop` - Linux桌面集成文件

## 前置要求

### 构建DEB包需要：
- `fakeroot`
- `dpkg-deb`
- `du`

在Debian/Ubuntu上安装：
```bash
sudo apt-get install fakeroot dpkg-dev
```

### 构建RPM包需要：
- `rpmbuild`
- `tar`
- `gzip`

在Fedora上安装：
```bash
sudo dnf install rpm-build
```

在RHEL/CentOS上安装：
```bash
sudo yum install rpm-build
```

## 使用方法

### 构建DEB包
```bash
cd packaging/linux
chmod +x build_deb.sh
./build_deb.sh
```
生成的文件将位于 `dist/PyStart_v{VERSION}_amd64.deb`

### 构建RPM包
```bash
cd packaging/linux
chmod +x build_rpm.sh
./build_rpm.sh
```
生成的文件将位于 `dist/PyStart_v{VERSION}_amd64.rpm`

## 安装

### 安装DEB包
```bash
sudo dpkg -i dist/PyStart_v{VERSION}_amd64.deb
sudo apt-get install -f  # 修复依赖（如果需要）
```

### 安装RPM包
```bash
sudo rpm -ivh dist/PyStart_v{VERSION}_amd64.rpm
```

## 卸载

### Debian/Ubuntu
```bash
sudo dpkg -r pystart
```

### Fedora/RHEL/CentOS
```bash
sudo rpm -e pystart
```

## 注意事项

1. 版本号从 `src/VERSION` 文件读取
2. 软件包将安装到 `/opt/PyStart` 目录
3. 可执行文件链接到 `/usr/bin/PyStart`
4. 桌面图标将自动安装
