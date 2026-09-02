Name:       nremote
Version:    1.5.0
Release:    0
Summary:    RPM package
License:    GPL-3.0
URL:        https://github.com/NDDev-OpenNetwork/nremote
Vendor:     nremote <info@nremote.com>
Requires:   gtk3 libxcb libXfixes alsa-lib libva2 gstreamer1-plugins-base
Recommends: libayatana-appindicator-gtk3 libxdo

# https://docs.fedoraproject.org/en-US/packaging-guidelines/Scriptlets/

%description
The best open-source remote desktop client software, written in Rust.

%prep
# we have no source, so nothing here

%build
# we have no source, so nothing here

%global __python %{__python3}

%install
mkdir -p %{buildroot}/usr/bin/
mkdir -p %{buildroot}/usr/share/nremote/
mkdir -p %{buildroot}/usr/share/nremote/files/
mkdir -p %{buildroot}/usr/share/icons/hicolor/256x256/apps/
mkdir -p %{buildroot}/usr/share/icons/hicolor/scalable/apps/
install -m 755 $HBB/target/release/nremote %{buildroot}/usr/bin/nremote
install $HBB/libsciter-gtk.so %{buildroot}/usr/share/nremote/libsciter-gtk.so
install $HBB/res/nremote.service %{buildroot}/usr/share/nremote/files/
install $HBB/res/128x128@2x.png %{buildroot}/usr/share/icons/hicolor/256x256/apps/nremote.png
install $HBB/res/scalable.svg %{buildroot}/usr/share/icons/hicolor/scalable/apps/nremote.svg
install $HBB/res/nremote.desktop %{buildroot}/usr/share/nremote/files/
install $HBB/res/nremote-link.desktop %{buildroot}/usr/share/nremote/files/

%files
/usr/bin/nremote
/usr/share/nremote/libsciter-gtk.so
/usr/share/nremote/files/nremote.service
/usr/share/icons/hicolor/256x256/apps/nremote.png
/usr/share/icons/hicolor/scalable/apps/nremote.svg
/usr/share/nremote/files/nremote.desktop
/usr/share/nremote/files/nremote-link.desktop
/usr/share/nremote/files/__pycache__/*

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
    rm /usr/share/applications/nremote.desktop || true
    rm /usr/share/applications/nremote-link.desktop || true
    update-desktop-database
  ;;
  1)
    # for upgrade
  ;;
esac
