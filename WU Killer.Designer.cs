namespace WU_Killer
{
    partial class WU_Killer
    {
        /// <summary>
        /// 必要なデザイナー変数です。
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// 使用中のリソースをすべてクリーンアップします。
        /// </summary>
        /// <param name="disposing">マネージド リソースを破棄する場合は true を指定し、その他の場合は false を指定します。</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows フォーム デザイナーで生成されたコード

        /// <summary>
        /// デザイナー サポートに必要なメソッドです。このメソッドの内容を
        /// コード エディターで変更しないでください。
        /// </summary>
        private void InitializeComponent()
        {
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(WU_Killer));
            this.Kill = new System.Windows.Forms.Button();
            this.Revert = new System.Windows.Forms.Button();
            this.SuspendLayout();
            // 
            // Kill
            // 
            this.Kill.Font = new System.Drawing.Font("MS UI Gothic", 60F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(128)));
            this.Kill.Location = new System.Drawing.Point(434, 156);
            this.Kill.Name = "Kill";
            this.Kill.Size = new System.Drawing.Size(336, 152);
            this.Kill.TabIndex = 0;
            this.Kill.Text = "殺";
            this.Kill.UseVisualStyleBackColor = true;
            this.Kill.Click += new System.EventHandler(this.Kill_Click);
            // 
            // Revert
            // 
            this.Revert.Font = new System.Drawing.Font("MS UI Gothic", 60F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(128)));
            this.Revert.Location = new System.Drawing.Point(42, 156);
            this.Revert.Name = "Revert";
            this.Revert.Size = new System.Drawing.Size(336, 152);
            this.Revert.TabIndex = 1;
            this.Revert.Text = "還";
            this.Revert.UseVisualStyleBackColor = true;
            this.Revert.Click += new System.EventHandler(this.Revert_Click);
            // 
            // WU_Killer
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(8F, 15F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(800, 450);
            this.Controls.Add(this.Revert);
            this.Controls.Add(this.Kill);
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.Name = "WU_Killer";
            this.Text = "WU Killer";
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.Button Kill;
        private System.Windows.Forms.Button Revert;
    }
}

