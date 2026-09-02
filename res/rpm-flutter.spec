Name:       nremote
Version:    1.5.0
Release:    0
Summary:    RPM package
License:    GPL-3.0
URL:        https://rustdesk.com
Vendor:     nremote <info@nremote.com>
Requires:   gtk3 libxcb libXfixes alsa-lib libva gstreamer1-plugins-base
Recommends: libayatana-appindicator-gtk3 libxdo
Provides:   libdesktop_drop_plugin.so()(64bit), libdesktop_multi_window_plugin.so()(64bit), libfile_selector_linux_plugin.so()(64bit), libflutter_custom_cursor_plugin.so()(64bit), libflutter_linux_gtk.so()(64bit), libscreen_retriever_plugin.so()(64bit), libtray_manager_plugin.so()(64bit), liburl_launcher_linux_plugin.so()(64bit), libwindow_manager_plugin.so()(64bit), libwindow_size_plugin.so()(64bit), libtexture_rgba_renderer_plugin.so()(64bit)

# https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/

%description
The best open-source remote desktop client software, written in Rust.

%prep
# we have no source, so nothing here

%build
# we have no source, so nothing here

# %global __python %{__python3}

%install

mkdir -p "%{buildroot}/usr/share/nremote" && cp -r ${HBB}/flutter/build/linux/x64/release/bundle/* -t "%{buildroot}/usr/share/nremote"
mkdir -p "%{buildroot}/usr/bin"
install -Dm 644 $HBB/res/nremote.service -t "%{buildroot}/usr/share/nremote/files"
install -Dm 644 $HBB/res/nremote.desktop -t "%{buildroot}/usr/share/nremote/files"
install -Dm 644 $HBB/res/nremote-link.desktop -t "%{buildroot}/usr/share/nremote/files"
install -Dm 644 $HBB/res/128x128@2x.png "%{buildroot}/usr/share/icons/hicolor/256x256/apps/nremote.png"
install -Dm 644 $HBB/res/scalable.svg "%{buildroot}/usr/share/icons/hicolor/scalable/apps/nremote.svg"

%files
/usr/share/nremote/*
/usr/share/nremote/files/nremote.service
/usr/share/icons/hicolor/256x256/apps/nremote.png
/usr/share/icons/hicolor/scalable/apps/nremote.svg
/usr/share/nremote/files/nremote.desktop
/usr/share/nremote/files/nremote-link.desktop

%changelog
# let's skip this for now

%pre
# can do something for centos7
case "$1" in
  1)
    # for install
  ;;
  2)
    # for upgrade
    systemctl stop nremote || true
  ;;
esac

%post
cp /usr/share/nremote/files/nremote.service /etc/systemd/system/nremote.service
cp /usr/share/nremote/files/nremote.desktop /usr/share/applications/
cp /usr/share/nremote/files/nremote-link.desktop /usr/share/applications/
ln -sf /usr/share/nremote/nremote /usr/bin/nremote
systemctl daemon-reload
systemctl enable nremote
systemctl start nremote
update-desktop-database

%preun
case "$1" in
  0)
    # for uninstall
    systemctl stop nremote || true
    systemctl disable nremote || true
    rm /etc/systemd/system/nremote.service || true
  ;;
  1)
    # for upgrade
  ;;
esac

%postun
case "$1" in
  0)
    # for uninstall
    rm /usr/bin/nremote || true
    rmdir /usr/lib/nremote || true
    rmdir /usr/local/nremote || true
    rmdir /usr/share/nremote || true
    rm /usr/share/applications/nremote.desktop || true
    rm /usr/share/applications/nremote-link.desktop || true
    update-desktop-database
  ;;
  1)
    # for upgrade
    rmdir /usr/lib/nremote || true
    rmdir /usr/local/nremote || true
  ;;
esac
