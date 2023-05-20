%define _disable_ld_no_undefined 1
%define url_ver %(echo %{version}|cut -d. -f1,2)

%define pppver %(rpm -q --qf "%{VERSION}" ppp)
%define pppddir %{_libdir}/pppd/%{pppver}
%define srcname ModemManager

%define major 0
%define libname %mklibname mm-glib %{major}
%define devname %mklibname mm-glib -d

%global __provides_exclude ^libmm-plugin-

%bcond_with vala

Summary:	Mobile broadband modem management service
Name:		modemmanager
Version:	1.20.6
Release:	1
License:	GPLv2+
Group:		System/Configuration/Networking
Url:		http://www.freedesktop.org/software/ModemManager
Source0:	https://gitlab.freedesktop.org/mobile-broadband/ModemManager/-/archive/%{version}/ModemManager-%{version}.tar.bz2
#Source0:	http://www.freedesktop.org/software/ModemManager/%{srcname}-%{version}.tar.xz
Source1:	%{name}.rpmlintrc
BuildRequires:	intltool
BuildRequires:	pkgconfig(polkit-gobject-1)
BuildRequires:	pkgconfig(dbus-glib-1)
BuildRequires:	pkgconfig(glib-2.0)
BuildRequires:	pkgconfig(gudev-1.0)
BuildRequires:	pkgconfig(qmi-glib) >= 1.26.0
BuildRequires:	pkgconfig(mbim-glib)
BuildRequires:	pkgconfig(gobject-introspection-1.0)
BuildRequires:	pkgconfig(libsystemd)
BuildRequires:	systemd-macros
BuildRequires:	autoconf-archive
BuildRequires:	xsltproc
%if %{with vala}
BuildRequires:	vala
BuildRequires:	pkgconfig(vapigen) >= 0.18
%endif
Requires:	mobile-broadband-provider-info
Requires:	usb_modeswitch

%description
The ModemManager service provides a consistent API to operate many different
modems, including mobile broadband (3G) devices.

%package -n %{libname}
Summary:	Shared libraries for %{name}
Group:		System/Libraries

%description -n %{libname}
Shared libraries for %{name}.

%package -n %{devname}
Summary:	Development package for %{name}
Group:		Development/Other
Requires:	%{libname} = %{version}-%{release}

%description -n %{devname}
Files for development with %{name}.

%prep
%autosetup -n %{srcname}-%{version} -p1

%build
%meson	\
	-Dpolkit=permissive \
	-Dudev=true \
	-Dudevdir==$(dirname %{_udevrulesdir}) \
	-Dsystemdsystemunitdir=%{_unitdir} \
	-Dsystemd_journal=true \
	-Dat_command_via_dbus=true \
	-Dbash_completion=true \
%if %{with vala}
	-Dvapi=true \
%else
	-Dvapi=false \
%endif
	-Dintrospection=true

%meson_build

%check
# The test suite wants to talk to stuff over dbus, which doesn't
# work in abf containers. Let's run the tests so we see when
# things go wrong without making it fatal.
#make check || :
meson test	

%install
%meson_install

# only used by test suite
rm -f %{buildroot}%{pppddir}/mm-test-pppd-plugin.so

# Let's relax polkit rules some more, beyond "permissive".
# It's useful for an admin user to be able to send SMS messages
# etc. without being "active".
mkdir -p %{buildroot}%{_datadir}/polkit-1/rules.d
cat >%{buildroot}%{_datadir}/polkit-1/rules.d/org.freedesktop.ModemManager1.rules <<'EOF'
polkit.addRule(function(action, subject) {
	if (action.id.startsWith("org.freedesktop.ModemManager1") && subject.isInGroup("wheel"))
		return polkit.Result.YES;
});
EOF

%find_lang %{srcname}

%triggerin -- %{name} < 1.0.0-1
/bin/systemctl enable %{srcname}.service
/bin/systemctl start %{srcname}.service

%post
%systemd_post ModemManager.service

%preun
%systemd_preun ModemManager.service

%postun
%systemd_postun ModemManager.service

%files -f %{srcname}.lang
%doc README AUTHORS
%{_sysconfdir}/dbus-1/system.d/org.freedesktop.ModemManager1.conf
%{_datadir}/dbus-1/interfaces/*.xml
%{_datadir}/dbus-1/system-services/org.freedesktop.ModemManager1.service
%{_datadir}/polkit-1/actions/org.freedesktop.ModemManager1.policy
%{_datadir}/polkit-1/rules.d/org.freedesktop.ModemManager1.rules
%dir %{_datadir}/ModemManager
%dir %{_datadir}/ModemManager/fcc-unlock.available.d
%dir %{_datadir}/ModemManager/connection.available.d
%{_datadir}/ModemManager/fcc-unlock.available.d/*
%{_datadir}/ModemManager/connection.available.d/*
%{_datadir}/ModemManager/*.conf
%{_iconsdir}/hicolor/22x22/apps/ModemManager.png
%{_bindir}/mmcli
%{_datadir}/bash-completion/completions/mmcli
%{_sbindir}/ModemManager
%dir %{_libdir}/%{srcname}
%{_libdir}/%{srcname}/*.so
%{_udevrulesdir}/*
%{_unitdir}/ModemManager.service
%doc %{_mandir}/man1/mmcli.1*
%doc %{_mandir}/man8/ModemManager.8*

%files -n %{libname}
%{_libdir}/libmm-glib.so.%{major}*

%files -n %{devname}
%dir %{_includedir}/libmm-glib
%dir %{_includedir}/%{srcname}
%{_includedir}/libmm-glib/*.h
%{_includedir}/%{srcname}/*.h
%{_libdir}/*.so
%{_libdir}/pkgconfig/*
%{_libdir}/girepository-1.0/ModemManager-1.0.typelib
%{_datadir}/gir-1.0/ModemManager-1.0.gir
%if %{with vala}
%{_datadir}/vala/vapi/libmm-glib.deps
%{_datadir}/vala/vapi/libmm-glib.vapi
%endif
