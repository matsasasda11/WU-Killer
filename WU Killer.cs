using System;
using System.Windows.Forms;
using System.ServiceProcess;
using Microsoft.Win32;

namespace WU_Killer {
    public partial class WU_Killer : Form {

        public WU_Killer() {
            InitializeComponent();
        }

        private void SetBusy(bool busy) {
            UseWaitCursor = busy;
            foreach (Control ctrl in Controls) {
                if (ctrl is Button)
                    ctrl.Enabled = !busy;
            }
            Cursor.Current = busy ? Cursors.WaitCursor : Cursors.Default;
            Application.DoEvents();
        }

        private void DisableWindowsUpdate(bool disable) {
            SetBusy(true);

            try {
                SetDword(@"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate", new[] {
                    ("DisableWindowsUpdateAccess", 1),
                    ("DoNotConnectToWindowsUpdateInternetLocations", 1),
                    ("SetDisableUXWUAccess", 1),
                    ("SetDisablePauseUXAccess", 1),
                    ("DisableOSUpgrade", 1),
                    ("ExcludeWUDriversInQualityUpdate", 1),
                    ("SetUpdateNotificationLevel", 2),
                    ("DisableDualScan", 1),
                }, disable);

                SetDword(@"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU", new[] {
                    ("NoAutoUpdate", 1),
                    ("AUOptions", 1),
                    ("NoAutoRebootWithLoggedOnUsers", 1),
                    ("EnableFeaturedSoftware", 0),
                    ("IncludeRecommendedUpdates", 0),
                    ("AutoInstallMinorUpdates", 0),
                    ("AllowMUUpdateService", 0),
                    ("NoAUAsDefaultShutdownOption", 1),
                    ("NoAUShutdownOption", 1),
                    ("AlwaysAutoRebootAtScheduledTime", 0),
                }, disable);

                SetDword(@"SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization", new[] {
                    ("DODownloadMode", 100),
                }, disable);

                SetDword(@"SOFTWARE\Policies\Microsoft\WindowsStore", new[] {
                    ("AutoDownload", 2),
                    ("RemoveWindowsStore", 1),
                }, disable);

                SetDword(@"SOFTWARE\Policies\Microsoft\Windows\DataCollection", new[] {
                    ("AllowTelemetry", 0),
                }, disable);

                SetDword(@"SOFTWARE\Policies\Microsoft\Windows\DriverSearching", new[] {
                    ("SearchOrderConfig", 0),
                    ("DontSearchWindowsUpdate", 1),
                }, disable);

                SetDword(@"SOFTWARE\Policies\Microsoft\Windows NT\Reliability", new[] {
                    ("ShutdownReasonOn", 0),
                    ("ShutdownReasonUI", 0),
                }, disable);

                foreach (string svc in new[] { "wuauserv", "UsoSvc", "WaaSMedicSvc", "BITS" }) {
                    SetServiceStartType(svc, disable);
                    ControlService(svc, disable);
                }
            } finally {
                SetBusy(false);
            }
            try {
                new System.Media.SoundPlayer(Environment.GetFolderPath(Environment.SpecialFolder.Windows) + @"\Media\Windows Exclamation.wav").Play();
            } catch { }
            MessageBox.Show("Windows Update を" + (disable ? "無" : "有") + "効化しました。",
                "完了", MessageBoxButtons.OK, MessageBoxIcon.Information);
            Application.Exit();
        }

        private void SetDword(string keyPath, (string name, int value)[] entries, bool disable) {
            try {
                using (RegistryKey key = Registry.LocalMachine.CreateSubKey(keyPath)) {
                    if (key == null) return;
                    foreach (var (name, value) in entries) {
                        if (disable)
                            key.SetValue(name, value, RegistryValueKind.DWord);
                        else
                            key.DeleteValue(name, false);
                    }
                }
            } catch { }
        }

        private void SetServiceStartType(string serviceName, bool disable) {
            try {
                using (RegistryKey key = Registry.LocalMachine.OpenSubKey(
                    $@"SYSTEM\CurrentControlSet\Services\{serviceName}", true)) {
                    key?.SetValue("Start", disable ? 4 : 2, RegistryValueKind.DWord);
                }
            } catch { }
        }

        private void ControlService(string serviceName, bool stop) {
            try {
                using (ServiceController sc = new ServiceController(serviceName)) {
                    if (stop && sc.Status == ServiceControllerStatus.Running) {
                        sc.Stop();
                        sc.WaitForStatus(ServiceControllerStatus.Stopped, TimeSpan.FromSeconds(10));
                    } else if (!stop && sc.Status == ServiceControllerStatus.Stopped) {
                        sc.Start();
                        sc.WaitForStatus(ServiceControllerStatus.Running, TimeSpan.FromSeconds(10));
                    }
                }
            } catch { }
        }

        private void Kill_Click(object sender, EventArgs e) {
            DisableWindowsUpdate(true);
        }

        private void Revert_Click(object sender, EventArgs e) {
            DisableWindowsUpdate(false);
        }
    }
}