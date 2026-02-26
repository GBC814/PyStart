#define AppName "PyStart"
#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif
#define AppPublisher "PyStart"
#define AppURL "https://github.com/PyStart"
#define AppExeName "PyStart.exe"

#ifndef OutputFileName
  #define OutputFileName "PyStart_Setup"
#endif

[Setup]
; 应用程序唯一标识符
AppId={{A7B9C1D2-E3F4-4567-8901-23456789ABCD}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
; 默认安装目录
DefaultDirName={autopf}\{#AppName}
; 禁用选择开始菜单文件夹页面
DisableProgramGroupPage=yes
; 安装包输出目录
OutputDir=..\..\dist
; 安装包文件名
OutputBaseFilename={#OutputFileName}
; 安装程序图标
SetupIconFile=..\..\assets\installer.ico
; 压缩方式
Compression=lzma
SolidCompression=yes
; 使用现代向导样式
WizardStyle=modern
; 禁用所有默认向导页面以使用自定义界面
DisableWelcomePage=yes
DisableDirPage=yes
DisableReadyPage=yes
DisableFinishedPage=no
; 卸载程序的图标显示
UninstallDisplayIcon={app}\assets\PyStart.ico

[Languages]
; 简体中文语言文件
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl"

[Messages]
; 简体中文语言文件
UninstallAppFullTitle=%1 卸载
UninstallAppTitle=%1 卸载

[Tasks]
; 移除显式任务定义，改用代码控制

[Files]
; 核心程序文件
Source: "..\..\dist\app\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; 配置文件
Source: "..\..\config.json"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
; 用户协议文件
Source: "..\..\src\LICENSE"; Flags: dontcopy
; 安装界面背景图
Source: "..\..\assets\installer.bmp"; Flags: dontcopy
; 应用程序 Logo
Source: "..\..\assets\PyStart.bmp"; DestDir: "{app}\assets"; Flags: ignoreversion
; 临时提取文件用于安装过程中的显示
Source: "..\..\assets\installer.bmp"; Flags: dontcopy
Source: "..\..\assets\PyStart.bmp"; Flags: dontcopy

[Icons]
; 开始菜单快捷方式
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
; 桌面快捷方式
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Check: IsShortcutSelected
; 卸载快捷方式
Name: "{autoprograms}\卸载 {#AppName}"; Filename: "{uninstallexe}"; IconFilename: "{app}\assets\PyStart.ico"

[Run]
; 安装完成后运行程序
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent; WorkingDir: "{app}"

[Code]
// API 声明
function ReleaseCapture(): Longint; external 'ReleaseCapture@user32.dll stdcall';
function SendMessage(hWnd: HWND; Msg: UINT; wParam: Longint; lParam: Longint): Longint; external 'SendMessageA@user32.dll stdcall';
function CreateRoundRectRgn(nLeftRect, nTopRect, nRightRect, nBottomRect, nWidthEllipse, nHeightEllipse: Integer): Longword; external 'CreateRoundRectRgn@gdi32.dll stdcall';
function SetWindowRgn(hWnd: HWND; hRgn: Longword; bRedraw: Boolean): Integer; external 'SetWindowRgn@user32.dll stdcall';
procedure ExitProcess(uExitCode: UINT); external 'ExitProcess@kernel32.dll stdcall';
type
  TMsg = record
    hwnd: HWND;
    message: UINT;
    wParam: Longint;
    lParam: Longint;
    time: DWORD;
    pt: TPoint;
  end;
function PeekMessage(var lpMsg: TMsg; hWnd: HWND; wMsgFilterMin, wMsgFilterMax, wRemoveMsg: UINT): BOOL; external 'PeekMessageW@user32.dll stdcall';
function TranslateMessage(var lpMsg: TMsg): BOOL; external 'TranslateMessage@user32.dll stdcall';
function DispatchMessage(var lpMsg: TMsg): Longint; external 'DispatchMessageW@user32.dll stdcall';

const
  VK_ESCAPE = $1B;
  WM_SYSCOMMAND = $0112;
  SC_MOVE = $F010;
  HTCAPTION = $0002;

var
  ShouldSilentExit: Boolean;
  InstallBtn: TPanel;
  InstallBtnText: TLabel;
  PathEdit: TEdit;
  PathEditPanel: TPanel;
  BrowseBtn: TPanel;
  BrowseBtnText: TLabel;
  AgreementCheck: TNewCheckBox;
  AgreementLabel: TLabel;
  ShortcutCheck: TNewCheckBox;
  CustomOptionsLabel: TLabel;
  PathLabel: TLabel;
  LogoPanel: TPanel;
  LogoImage: TBitmapImage;
  BgImage: TBitmapImage;
  TitleLabel: TLabel;
  CloseBtnLabel: TLabel;
  LangEdit: TEdit;
  LangArrow: TLabel;
  LangLabel: TLabel;
  LangComboPanel: TPanel;
  LangDropPanel: TPanel;
  CHLangItem, ENLangItem: TLabel;
  SelectedLangIndex: Integer;
  IsExpanded: Boolean;
  FinishedLabel: TLabel;
  LaunchCheck: TNewCheckBox;
  FinishBtn: TPanel;
  FinishBtnText: TLabel;
  ProgressBar: TNewProgressBar;
  StatusLabel: TLabel;
  Installing: Boolean;
  MeasureLabel: TLabel;

  // 卸载界面组件
  UnHomePanel: TPanel;
  UnProgressPanel: TPanel;
  UnQuickBtn: TPanel;
  UnQuickBtnText: TLabel;
  UnTitleLabel: TLabel;
  UnProgressTitleLabel: TLabel;
  UnStatusLabel: TLabel;
  UnProgressBar: TNewProgressBar;
  UnFinished: Boolean;
  UnSelectedLangIndex: Integer;
  CanUninstall: Boolean;
  IsAborted: Boolean;

// 语言文本定义
function GetText(Key: string): string;
begin
  if SelectedLangIndex = 0 then // 简体中文
  begin
    if Key = 'InstallNow' then Result := '立即安装';
    if Key = 'Agreement' then Result := '我已阅读并同意 ';
    if Key = 'AgreementLink' then Result := '用户协议';
    if Key = 'CustomOptions' then Result := '自定义安装选项';
    if Key = 'InstallPath' then Result := '安装位置:';
    if Key = 'Browse' then Result := '浏览';
    if Key = 'Shortcut' then Result := '创建桌面快捷方式';
    if Key = 'Installing' then Result := '正在安装...';
    if Key = 'Finished' then Result := '安装完成';
    if Key = 'Launch' then Result := '运行 PyStart';
    if Key = 'FinishBtn' then Result := '立即体验';
  end
  else // English
  begin
    if Key = 'InstallNow' then Result := 'Install Now';
    if Key = 'Agreement' then Result := 'I have read and agree to the ';
    if Key = 'AgreementLink' then Result := 'agreement';
    if Key = 'CustomOptions' then Result := 'Custom Options';
    if Key = 'InstallPath' then Result := 'Install Path:';
    if Key = 'Browse' then Result := 'Browse';
    if Key = 'Shortcut' then Result := 'Create Desktop Shortcut';
    if Key = 'Installing' then Result := 'Installing...';
    if Key = 'Finished' then Result := 'Installation Finished';
    if Key = 'Launch' then Result := 'Launch PyStart';
    if Key = 'FinishBtn' then Result := 'Finish';
  end;
end;

procedure RefreshLanguage();
var
  TW: Integer;
begin
  InstallBtnText.Caption := GetText('InstallNow');
  
  // 测量协议复选框文字宽度
  AgreementCheck.Caption := GetText('Agreement');
  MeasureLabel.Font.Name := AgreementCheck.Font.Name;
  MeasureLabel.Font.Size := AgreementCheck.Font.Size;
  MeasureLabel.Font.Style := AgreementCheck.Font.Style;
  MeasureLabel.Caption := AgreementCheck.Caption;
  TW := MeasureLabel.Width;
  
  // Inno Setup 的 CheckBox 图标宽度约为 16px，加上间距约 20-24px
  // 设置宽度刚好包住文字
  AgreementCheck.Width := 24 + TW + 5;
  AgreementLabel.Caption := GetText('AgreementLink');
  AgreementLabel.AutoSize := True;
  AgreementLabel.Left := AgreementCheck.Left + 22 + TW + 10;
  
  CustomOptionsLabel.Caption := GetText('CustomOptions');
  CustomOptionsLabel.AutoSize := True;
  CustomOptionsLabel.Left := WizardForm.ClientWidth - CustomOptionsLabel.Width - 40;
  
  PathLabel.Caption := GetText('InstallPath');
  BrowseBtnText.Caption := GetText('Browse');
  
  // 测量快捷方式复选框
  ShortcutCheck.Caption := GetText('Shortcut');
  MeasureLabel.Caption := ShortcutCheck.Caption;
  ShortcutCheck.Width := 24 + MeasureLabel.Width + 10;
  
  FinishedLabel.Caption := GetText('Finished');
  
  // 测量运行程序复选框
  LaunchCheck.Caption := GetText('Launch');
  MeasureLabel.Caption := LaunchCheck.Caption;
  LaunchCheck.Width := 24 + MeasureLabel.Width + 10;
  // 居中显示运行复选框
  LaunchCheck.Left := (WizardForm.ClientWidth - LaunchCheck.Width) div 2;
  
  FinishBtnText.Caption := GetText('FinishBtn');
  
  if Installing then
    StatusLabel.Caption := GetText('Installing');
end;

procedure CHItemClick(Sender: TObject);
begin
  SelectedLangIndex := 0;
  LangEdit.Text := '简体中文';
  LangDropPanel.Visible := False;
  RefreshLanguage();
end;

procedure ENItemClick(Sender: TObject);
begin
  SelectedLangIndex := 1;
  LangEdit.Text := 'English';
  LangDropPanel.Visible := False;
  RefreshLanguage();
end;

procedure LangSelectorClick(Sender: TObject);
begin
  LangDropPanel.Visible := not LangDropPanel.Visible;
  if LangDropPanel.Visible then
    LangDropPanel.BringToFront;
end;

// 进度条更新
procedure CurInstallProgressChanged(CurProgress, MaxProgress: Integer);
begin
  if ProgressBar <> nil then
  begin
    ProgressBar.Position := CurProgress;
    ProgressBar.Max := MaxProgress;
  end;
end;

// 应用圆角
procedure ApplyRoundedCorners(Control: TWinControl; Radius: Integer);
var
  hRgn: Longword;
begin
  if (Control <> nil) and (Control.Handle <> 0) then
  begin
    hRgn := CreateRoundRectRgn(0, 0, Control.ClientWidth, Control.ClientHeight, Radius, Radius);
    SetWindowRgn(Control.Handle, hRgn, True);
  end;
end;

// 窗口拖拽事件
procedure BgMouseDown(Sender: TObject; Button: TMouseButton; Shift: TShiftState; X, Y: Integer);
begin
  if Button = mbLeft then
  begin
    ReleaseCapture();
    SendMessage(WizardForm.Handle, WM_SYSCOMMAND, SC_MOVE + HTCAPTION, 0);
  end;
end;

// 键盘事件：支持 Esc 退出
procedure FormKeyDown(Sender: TObject; var Key: Word; Shift: TShiftState);
begin
  if Key = VK_ESCAPE then
  begin
    if WizardForm.CurPageID = wpFinished then
      ExitProcess(0)
    else
      WizardForm.Close;
  end;
end;

// 关闭按钮点击事件
procedure CloseBtnClick(Sender: TObject);
begin
  if WizardForm.CurPageID = wpFinished then
    ExitProcess(0)
  else
    WizardForm.Close;
end;

procedure UnCloseBtnClick(Sender: TObject);
begin
  if not CanUninstall then
  begin
    IsAborted := True;
    UninstallProgressForm.Close;
  end
  else
  begin
    // 卸载过程中点击关闭，直接退出进程
    ExitProcess(0);
  end;
end;

// 键盘事件：支持 Esc 退出
procedure UninstallFormKeyDown(Sender: TObject; var Key: Word; Shift: TShiftState);
begin
  if Key = VK_ESCAPE then
  begin
    if not CanUninstall then
    begin
      IsAborted := True;
      UninstallProgressForm.Close;
    end
    else
    begin
      // 卸载过程中按 ESC，直接退出进程
      ExitProcess(0);
    end;
  end;
end;

procedure CancelButtonClick(CurPageID: Integer; var Cancel, Confirm: Boolean);
begin
  if CurPageID = wpFinished then
  begin
    ExitProcess(0);
  end;
  Cancel := True;
  Confirm := False;
end;

// 用于控制桌面快捷方式生成的 Check 函数
function IsShortcutSelected(): Boolean;
begin
  Result := ShortcutCheck.Checked;
end;

// 浏览按钮点击事件：选择安装路径
procedure BrowseBtnClick(Sender: TObject);
var
  Dir: string;
begin
  Dir := PathEdit.Text;
  if BrowseForFolder('选择安装目录', Dir, True) then
    PathEdit.Text := Dir;
end;

// 显示用户协议对话框
procedure ShowAgreementClick(Sender: TObject);
var
  LicenseText: String;
  SL: TStringList;
begin
  ExtractTemporaryFile('LICENSE');
  SL := TStringList.Create;
  try
    if FileExists(ExpandConstant('{tmp}\LICENSE')) then
    begin
      try
        SL.LoadFromFile(ExpandConstant('{tmp}\LICENSE'));
        LicenseText := SL.Text;
        MsgBox(LicenseText, mbInformation, MB_OK);
      except
        if SelectedLangIndex = 0 then
          MsgBox('读取用户协议文件失败。', mbError, MB_OK)
        else
          MsgBox('Failed to read user agreement file.', mbError, MB_OK);
      end;
    end
    else
    begin
      if SelectedLangIndex = 0 then
        MsgBox('找不到用户协议文件。', mbError, MB_OK)
      else
        MsgBox('User agreement file not found.', mbError, MB_OK);
    end;
  finally
    SL.Free;
  end;
end;

// 实际执行安装的逻辑
procedure ProceedToInstall();
begin
  if not AgreementCheck.Checked then
  begin
    if SelectedLangIndex = 0 then
      MsgBox('请先阅读并同意用户协议', mbInformation, MB_OK)
    else
      MsgBox('Please read and agree to the agreement first', mbInformation, MB_OK);
    Exit;
  end;
  
  Installing := True;
  
  // 隐藏安装前组件
  InstallBtn.Visible := False;
  AgreementCheck.Visible := False;
  AgreementLabel.Visible := False;
  CustomOptionsLabel.Visible := False;
  PathLabel.Visible := False;
  PathEditPanel.Visible := False;
  BrowseBtn.Visible := False;
  ShortcutCheck.Visible := False;
  LangComboPanel.Visible := False;
  LangDropPanel.Visible := False;
  
  // 显示进度条组件
  StatusLabel.Caption := GetText('Installing');
  StatusLabel.Visible := True;
  ProgressBar.Visible := True;
  
  WizardForm.DirEdit.Text := PathEdit.Text;
  
  // 延迟一小会儿让 UI 更新，然后开始安装
  WizardForm.NextButton.OnClick(WizardForm.NextButton);
end;

// 模拟按钮点击事件
procedure InstallBtnClick(Sender: TObject);
begin
  ProceedToInstall();
end;

// 自定义安装选项点击事件：显示/隐藏路径选择
procedure CustomOptionsClick(Sender: TObject);
begin
  IsExpanded := not IsExpanded;
  if IsExpanded then
  begin
    WizardForm.ClientHeight := 624;
    PathLabel.Visible := True;
    PathEditPanel.Visible := True;
    BrowseBtn.Visible := True;
    ShortcutCheck.Visible := True;
  end
  else
  begin
    WizardForm.ClientHeight := 524;
    PathLabel.Visible := False;
    PathEditPanel.Visible := False;
    BrowseBtn.Visible := False;
    ShortcutCheck.Visible := False;
  end;
  // 重新应用圆角，使用最新的圆角半径
  ApplyRoundedCorners(WizardForm, 30);
end;

// 完成按钮点击
procedure FinishBtnClick(Sender: TObject);
begin
  if LaunchCheck.Checked then
  begin
    // 如果勾选了运行程序，则在退出后执行
    WizardForm.NextButton.OnClick(WizardForm.NextButton);
  end
  else
  begin
    // 如果没有勾选运行程序，则直接退出
    ExitProcess(0);
  end;
end;

// 初始化安装向导界面
procedure InitializeWizard();
begin
  IsExpanded := False;
  Installing := False;
  ShouldSilentExit := False;

  // 创建一个隐藏的 Label 用于测量文字宽度
  MeasureLabel := TLabel.Create(WizardForm);
  MeasureLabel.Parent := WizardForm;
  MeasureLabel.Visible := False;
  MeasureLabel.AutoSize := True;

  // 移除标准边框
  WizardForm.BorderStyle := bsNone;
  WizardForm.OnKeyDown := @FormKeyDown;
  WizardForm.KeyPreview := True;
  
  // 隐藏原始向导组件，但保持取消按钮可用
  WizardForm.OuterNotebook.Hide;
  WizardForm.NextButton.Hide;
  WizardForm.BackButton.Hide;
  WizardForm.CancelButton.SetBounds(-100, -100, 0, 0);
  WizardForm.CancelButton.Enabled := True;
  
  // 设置窗口尺寸
  WizardForm.ClientWidth := 900;
  WizardForm.ClientHeight := 524;
  ApplyRoundedCorners(WizardForm, 30);

  // 设置背景图
  BgImage := TBitmapImage.Create(WizardForm);
  BgImage.Parent := WizardForm;
  BgImage.SetBounds(0, 0, 900, 624);
  BgImage.Stretch := True;
  ExtractTemporaryFile('installer.bmp');
  BgImage.Bitmap.LoadFromFile(ExpandConstant('{tmp}\installer.bmp'));

  // 设置自定义关闭按钮
  CloseBtnLabel := TLabel.Create(WizardForm);
  CloseBtnLabel.Parent := WizardForm;
  CloseBtnLabel.Caption := '×';
  CloseBtnLabel.Font.Name := 'Arial';
  CloseBtnLabel.Font.Size := 24;
  CloseBtnLabel.Font.Color := clWhite;
  CloseBtnLabel.Transparent := True;
  CloseBtnLabel.Cursor := crHand;
  CloseBtnLabel.Alignment := taCenter;
  CloseBtnLabel.SetBounds(WizardForm.ClientWidth - 50, 10, 40, 40);
  CloseBtnLabel.OnClick := @CloseBtnClick;
  CloseBtnLabel.BringToFront;

  // 设置语言选择框
  SelectedLangIndex := 0;
  LangComboPanel := TPanel.Create(WizardForm);
  LangComboPanel.Parent := WizardForm;
  LangComboPanel.SetBounds(WizardForm.ClientWidth - 200, 20, 130, 30);
  LangComboPanel.Color := $00E68B12; 
  LangComboPanel.ParentBackground := False;
  LangComboPanel.ParentColor := False;
  LangComboPanel.BevelOuter := bvNone;
  LangComboPanel.Cursor := crHand;
  LangComboPanel.OnClick := @LangSelectorClick;
  ApplyRoundedCorners(LangComboPanel, 5);

  LangEdit := TEdit.Create(LangComboPanel);
  LangEdit.Parent := LangComboPanel;
  LangEdit.SetBounds(5, 3, 105, 24);
  LangEdit.BorderStyle := bsNone;
  LangEdit.ReadOnly := True;
  LangEdit.Color := $00E68B12;
  LangEdit.Font.Name := 'Microsoft YaHei UI';
  LangEdit.Font.Size := 10;
  LangEdit.Font.Color := clWhite;
  LangEdit.Text := '简体中文';
  LangEdit.Cursor := crHand;
  LangEdit.OnClick := @LangSelectorClick;

  LangArrow := TLabel.Create(LangComboPanel);
  LangArrow.Parent := LangComboPanel;
  LangArrow.SetBounds(110, 3, 20, 24);
  LangArrow.Caption := '▼';
  LangArrow.Font.Color := clWhite;
  LangArrow.Transparent := True;
  LangArrow.Cursor := crHand;
  LangArrow.Layout := tlCenter;
  LangArrow.OnClick := @LangSelectorClick;

  // 创建自定义下拉列表面板
  LangDropPanel := TPanel.Create(WizardForm);
  LangDropPanel.Parent := WizardForm;
  LangDropPanel.SetBounds(LangComboPanel.Left, LangComboPanel.Top + LangComboPanel.Height, LangComboPanel.Width, 60);
  LangDropPanel.Color := $00E68B12;
  LangDropPanel.ParentBackground := False;
  LangDropPanel.ParentColor := False;
  LangDropPanel.BevelOuter := bvNone;
  LangDropPanel.Visible := False;
  ApplyRoundedCorners(LangDropPanel, 5);

  CHLangItem := TLabel.Create(LangDropPanel);
  CHLangItem.Parent := LangDropPanel;
  CHLangItem.SetBounds(0, 0, LangDropPanel.Width, 30);
  CHLangItem.AutoSize := False;
  CHLangItem.Alignment := taCenter;
  CHLangItem.Layout := tlCenter;
  CHLangItem.Caption := '简体中文';
  CHLangItem.Font.Name := 'Microsoft YaHei UI';
  CHLangItem.Font.Size := 10;
  CHLangItem.Font.Color := clWhite;
  CHLangItem.Cursor := crHand;
  CHLangItem.OnClick := @CHItemClick;

  ENLangItem := TLabel.Create(LangDropPanel);
  ENLangItem.Parent := LangDropPanel;
  ENLangItem.SetBounds(0, 30, LangDropPanel.Width, 30);
  ENLangItem.AutoSize := False;
  ENLangItem.Alignment := taCenter;
  ENLangItem.Layout := tlCenter;
  ENLangItem.Caption := 'English';
  ENLangItem.Font.Name := 'Microsoft YaHei UI';
  ENLangItem.Font.Size := 10;
  ENLangItem.Font.Color := clWhite;
  ENLangItem.Cursor := crHand;
  ENLangItem.OnClick := @ENItemClick;
  
  LangComboPanel.BringToFront;

  // 设置 Logo 容器
  LogoPanel := TPanel.Create(WizardForm);
  LogoPanel.Parent := WizardForm;
  LogoPanel.SetBounds((900 - 120) div 2, 50, 120, 120); 
  LogoPanel.BevelOuter := bvNone;
  LogoPanel.ParentBackground := True;
  ApplyRoundedCorners(LogoPanel, 60);

  LogoImage := TBitmapImage.Create(LogoPanel);
  LogoImage.Parent := LogoPanel;
  LogoImage.SetBounds(0, 0, 120, 120);
  LogoImage.Stretch := True;
  ExtractTemporaryFile('PyStart.bmp');
  LogoImage.Bitmap.LoadFromFile(ExpandConstant('{tmp}\PyStart.bmp'));

  // 设置软件名称标题
  TitleLabel := TLabel.Create(WizardForm);
  TitleLabel.Parent := WizardForm;
  TitleLabel.Caption := 'PyStart';
  TitleLabel.Font.Name := 'Microsoft YaHei UI';
  TitleLabel.Font.Size := 36;
  TitleLabel.Font.Style := [fsBold];
  TitleLabel.Font.Color := clWhite;
  TitleLabel.Transparent := True;
  TitleLabel.AutoSize := True;
  TitleLabel.Left := (900 - TitleLabel.Width) div 2;
  TitleLabel.Top := 180;

  // “立即安装”按钮
  InstallBtn := TPanel.Create(WizardForm);
  InstallBtn.Parent := WizardForm;
  InstallBtn.SetBounds((900 - 320) div 2, 320, 320, 60); 
  InstallBtn.Color := $00EB8F00;
  InstallBtn.ParentBackground := False;
  InstallBtn.BevelOuter := bvNone;
  InstallBtn.OnClick := @InstallBtnClick;
  InstallBtn.Cursor := crHand;
  ApplyRoundedCorners(InstallBtn, 8); 

  InstallBtnText := TLabel.Create(InstallBtn);
  InstallBtnText.Parent := InstallBtn;
  InstallBtnText.Caption := '立即安装';
  InstallBtnText.Font.Name := 'Microsoft YaHei UI';
  InstallBtnText.Font.Size := 16;
  InstallBtnText.Font.Style := [fsBold];
  InstallBtnText.Font.Color := clWhite;
  InstallBtnText.Alignment := taCenter;
  InstallBtnText.AutoSize := False;
  InstallBtnText.SetBounds(0, 0, 320, 60);
  InstallBtnText.Layout := tlCenter;
  InstallBtnText.OnClick := @InstallBtnClick;
  InstallBtnText.Cursor := crHand;
  InstallBtnText.Transparent := True;

  // 用户协议勾选框
  AgreementCheck := TNewCheckBox.Create(WizardForm);
  AgreementCheck.Parent := WizardForm;
  AgreementCheck.SetBounds(20, 450, 220, 30);
  AgreementCheck.Caption := GetText('Agreement');
  AgreementCheck.Checked := True;
  AgreementCheck.Font.Name := 'Microsoft YaHei UI';
  AgreementCheck.Font.Size := 10;
  AgreementCheck.Font.Color := $002D2D2D;

  AgreementLabel := TLabel.Create(WizardForm);
  AgreementLabel.Parent := WizardForm;
  AgreementLabel.Caption := GetText('AgreementLink');
  AgreementLabel.SetBounds(AgreementCheck.Left + 125, 450, 100, 30);
  AgreementLabel.Font.Name := 'Microsoft YaHei UI';
  AgreementLabel.Font.Size := 10;
  AgreementLabel.Font.Color := $00E68B12;
  AgreementLabel.Font.Style := [fsUnderline];
  AgreementLabel.Cursor := crHand;
  AgreementLabel.OnClick := @ShowAgreementClick;
  AgreementLabel.Transparent := True;
  AgreementLabel.Layout := tlCenter;

  // 自定义安装选项链接
  CustomOptionsLabel := TLabel.Create(WizardForm);
  CustomOptionsLabel.Parent := WizardForm;
  CustomOptionsLabel.SetBounds(740, 450, 120, 30);
  CustomOptionsLabel.Caption := '自定义安装选项';
  CustomOptionsLabel.Cursor := crHand;
  CustomOptionsLabel.Font.Name := 'Microsoft YaHei UI';
  CustomOptionsLabel.Font.Size := 10;
  // CustomOptionsLabel.Font.Color := clWhite;
  CustomOptionsLabel.Font.Color := $002D2D2D;
  CustomOptionsLabel.Font.Style := [fsUnderline];
  CustomOptionsLabel.OnClick := @CustomOptionsClick;
  CustomOptionsLabel.Transparent := True;

  // 安装路径选择组件
  PathLabel := TLabel.Create(WizardForm);
  PathLabel.Parent := WizardForm;
  PathLabel.SetBounds(20, 524, 80, 40);
  PathLabel.Layout := tlCenter;
  PathLabel.Caption := GetText('InstallPath');
  PathLabel.Font.Name := 'Microsoft YaHei UI';
  PathLabel.Font.Size := 10;
  PathLabel.Font.Color := $002D2D2D;
  PathLabel.Transparent := True;
  PathLabel.Visible := False;

  PathEditPanel := TPanel.Create(WizardForm);
  PathEditPanel.Parent := WizardForm;
  PathEditPanel.SetBounds(150, 524, 600, 40);
  PathEditPanel.Color := $00F0F0F0;
  PathEditPanel.ParentBackground := False;
  PathEditPanel.BevelOuter := bvNone;
  PathEditPanel.Visible := False;
  ApplyRoundedCorners(PathEditPanel, 8);

  PathEdit := TEdit.Create(PathEditPanel);
  PathEdit.Parent := PathEditPanel;
  PathEdit.SetBounds(10, 8, 580, 24);
  PathEdit.BorderStyle := bsNone;
  PathEdit.Color := $00F0F0F0;
  PathEdit.Font.Name := 'Microsoft YaHei UI';
  PathEdit.Font.Size := 10;
  PathEdit.Font.Color := $002D2D2D;
  PathEdit.Text := ExpandConstant('{autopf}\{#AppName}');

  BrowseBtn := TPanel.Create(WizardForm);
  BrowseBtn.Parent := WizardForm;
  BrowseBtn.SetBounds(770, 524, 110, 40);
  BrowseBtn.Color := $0012C4FF;
  BrowseBtn.ParentBackground := False;
  BrowseBtn.BevelOuter := bvNone;
  BrowseBtn.OnClick := @BrowseBtnClick;
  BrowseBtn.Cursor := crHand;
  BrowseBtn.Visible := False;
  ApplyRoundedCorners(BrowseBtn, 8);

  BrowseBtnText := TLabel.Create(BrowseBtn);
  BrowseBtnText.Parent := BrowseBtn;
  BrowseBtnText.Caption := GetText('Browse');
  BrowseBtnText.Font.Name := 'Microsoft YaHei UI';
  BrowseBtnText.Font.Size := 8;
  BrowseBtnText.Font.Style := [fsBold];
  BrowseBtnText.Font.Color := $002D2D2D;
  BrowseBtnText.Alignment := taCenter;
  BrowseBtnText.AutoSize := False;
  BrowseBtnText.SetBounds(0, 10, 110, 20);
  BrowseBtnText.OnClick := @BrowseBtnClick;
  BrowseBtnText.Cursor := crHand;
  BrowseBtnText.Transparent := True;

  // 进度条和状态标签
  StatusLabel := TLabel.Create(WizardForm);
  StatusLabel.Parent := WizardForm;
  StatusLabel.SetBounds(150, 300, 600, 30);
  StatusLabel.AutoSize := False;
  StatusLabel.Alignment := taCenter;
  StatusLabel.Caption := '';
  StatusLabel.Font.Name := 'Microsoft YaHei UI';
  StatusLabel.Font.Size := 12;
  StatusLabel.Font.Color := $002D2D2D;
  StatusLabel.Transparent := True;
  StatusLabel.Visible := False;

  ProgressBar := TNewProgressBar.Create(WizardForm);
  ProgressBar.Parent := WizardForm;
  ProgressBar.SetBounds(150, 340, 600, 20);
  ProgressBar.Visible := False;

  // 创建快捷方式勾选框
  ShortcutCheck := TNewCheckBox.Create(WizardForm);
  ShortcutCheck.Parent := WizardForm;
  ShortcutCheck.SetBounds(20, 590, 350, 30);
  ShortcutCheck.Caption := '创建桌面快捷方式';
  ShortcutCheck.Checked := True;
  ShortcutCheck.Font.Name := 'Microsoft YaHei UI';
  ShortcutCheck.Font.Size := 10;
  ShortcutCheck.Font.Color := $002D2D2D;
  ShortcutCheck.Visible := False;

  // --- 安装完成界面组件 ---
  FinishedLabel := TLabel.Create(WizardForm);
  FinishedLabel.Parent := WizardForm;
  FinishedLabel.SetBounds(0, 190, 900, 80);
  FinishedLabel.AutoSize := False;
  FinishedLabel.Alignment := taCenter;
  FinishedLabel.Caption := '安装完成';
  FinishedLabel.Font.Name := 'Microsoft YaHei UI';
  FinishedLabel.Font.Size := 32;
  FinishedLabel.Font.Style := [fsBold];
  // FinishedLabel.Font.Color := clWhite;
  FinishedLabel.Font.Color := $002D2D2D;
  FinishedLabel.Transparent := True;
  FinishedLabel.Visible := False;

  LaunchCheck := TNewCheckBox.Create(WizardForm);
  LaunchCheck.Parent := WizardForm;
  LaunchCheck.SetBounds((900 - 150) div 2, 290, 150, 25);
  LaunchCheck.Caption := '运行 PyStart';
  LaunchCheck.Checked := True;
  LaunchCheck.Font.Name := 'Microsoft YaHei UI';
  LaunchCheck.Font.Size := 10;
  LaunchCheck.Font.Color := $002D2D2D;
  LaunchCheck.Visible := False;

  FinishBtn := TPanel.Create(WizardForm);
  FinishBtn.Parent := WizardForm;
  FinishBtn.SetBounds((900 - 320) div 2, 340, 320, 60);
  FinishBtn.Color := $0000B9FF;
  FinishBtn.ParentBackground := False;
  FinishBtn.BevelOuter := bvNone;
  FinishBtn.OnClick := @FinishBtnClick;
  FinishBtn.Cursor := crHand;
  ApplyRoundedCorners(FinishBtn, 10);
  FinishBtn.Visible := False;

  FinishBtnText := TLabel.Create(FinishBtn);
  FinishBtnText.Parent := FinishBtn;
  FinishBtnText.Caption := '立即体验';
  FinishBtnText.Font.Name := 'Microsoft YaHei UI';
  FinishBtnText.Font.Size := 18;
  FinishBtnText.Font.Style := [fsBold];
  FinishBtnText.Font.Color := $002D2D2D;
  FinishBtnText.Alignment := taCenter;
  FinishBtnText.AutoSize := False;
  FinishBtnText.SetBounds(0, 0, 320, 60);
  FinishBtnText.Layout := tlCenter;
  FinishBtnText.OnClick := @FinishBtnClick;
  FinishBtnText.Cursor := crHand;
  FinishBtnText.Transparent := True;

  RefreshLanguage();
end;

// 卸载界面语言文本
function GetUnText(Key: string): string;
begin
  if UnSelectedLangIndex = 0 then
  begin
    if Key = 'QuickUninstall' then Result := '快速卸载';
    if Key = 'Uninstalling' then Result := '正在卸载...';
    if Key = 'Finished' then Result := '卸载完成';
  end
  else
  begin
    if Key = 'QuickUninstall' then Result := 'Quick Uninstall';
    if Key = 'Uninstalling' then Result := 'Uninstalling...';
    if Key = 'Finished' then Result := 'Uninstall Finished';
  end;
end;

// 获取主程序配置的语言
function GetConfigLanguage(): string;
var
  ConfigPath: string;
  Lines: TArrayOfString;
  I, P: Integer;
  Line: string;
begin
  Result := 'zh_CN';
  
  // 尝试读取安装目录下的 config.json
  ConfigPath := ExpandConstant('{app}\config.json');
  if not FileExists(ConfigPath) then
  begin
    // 尝试读取 APPDATA 下的 config.json
    ConfigPath := ExpandConstant('{userappdata}\{#AppName}\config.json');
  end;

  if FileExists(ConfigPath) then
  begin
    if LoadStringsFromFile(ConfigPath, Lines) then
    begin
      for I := 0 to GetArrayLength(Lines) - 1 do
      begin
        Line := Lines[I];
        P := Pos('"language"', Line);
        if P > 0 then
        begin
          // 简单解析 "language": "xxx"
          P := Pos(':', Line);
          if P > 0 then
          begin
            Line := Copy(Line, P + 1, Length(Line));
            P := Pos('"', Line);
            if P > 0 then
            begin
              Line := Copy(Line, P + 1, Length(Line));
              P := Pos('"', Line);
              if P > 0 then
              begin
                Result := Copy(Line, 1, P - 1);
                Exit;
              end;
            end;
          end;
        end;
      end;
    end;
  end;
end;

procedure RefreshUninstallLanguage();
begin
  try
    if (UnQuickBtnText <> nil) then
      UnQuickBtnText.Caption := GetUnText('QuickUninstall');
      
    if (UnStatusLabel <> nil) then
    begin
      if UnFinished then
        UnStatusLabel.Caption := GetUnText('Finished')
      else
        UnStatusLabel.Caption := GetUnText('Uninstalling');
    end;
  except
    // 忽略可能的指针错误
  end;
end;

procedure UnQuickBtnClick(Sender: TObject);
begin
  CanUninstall := True;
  UnHomePanel.Visible := False;
  UnProgressPanel.Visible := True;
  UnStatusLabel.Visible := True;
  UninstallProgressForm.ProgressBar.Visible := True;
  UninstallProgressForm.ProgressBar.BringToFront;
  RefreshUninstallLanguage();
end;

// 初始化卸载
function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  // 如果不是静默模式，则静默启动自己以跳过确认对话框
  if not UninstallSilent then
  begin
    if ShellExec('', ExpandConstant('{uninstallexe}'), '/SILENT', '', SW_SHOW, ewNoWait, ResultCode) then
    begin
      Result := False;
    end;
  end;
end;

procedure InitializeUninstallProgressForm();
var
  UnBgImage: TBitmapImage;
  UnCloseBtn: TLabel;
  Lang: string;
begin
  UnSelectedLangIndex := 0;
  CanUninstall := False;
  IsAborted := False;

  // 在静默模式下强制显示卸载窗体
  if UninstallSilent then
  begin
    UninstallProgressForm.Visible := True;
  end;

  // 检测语言
  Lang := GetConfigLanguage();
  if (Lang = 'zh_CN') or (Lang = 'zh_Hans') then
    UnSelectedLangIndex := 0
  else
    UnSelectedLangIndex := 1;

  UninstallProgressForm.BorderStyle := bsNone;
  UninstallProgressForm.OnKeyDown := @UninstallFormKeyDown;
  UninstallProgressForm.KeyPreview := True;
  
  UninstallProgressForm.CancelButton.SetBounds(-100, -100, 0, 0);
  UninstallProgressForm.CancelButton.Visible := True;
  UninstallProgressForm.CancelButton.Enabled := True;
  
  UninstallProgressForm.ClientWidth := 900;
  UninstallProgressForm.ClientHeight := 524;
  ApplyRoundedCorners(UninstallProgressForm, 30);

  // 背景色
  UninstallProgressForm.Color := $002E3DFF; 

  // 背景图
  UnBgImage := TBitmapImage.Create(UninstallProgressForm);
  UnBgImage.Parent := UninstallProgressForm;
  UnBgImage.SetBounds(0, 0, 900, 524);
  UnBgImage.Stretch := True;
  if FileExists(ExpandConstant('{app}\assets\installer_gradient.bmp')) then
    UnBgImage.Bitmap.LoadFromFile(ExpandConstant('{app}\assets\installer_gradient.bmp'))
  else if FileExists(ExpandConstant('{app}\assets\installer.bmp')) then
    UnBgImage.Bitmap.LoadFromFile(ExpandConstant('{app}\assets\installer.bmp'));

  // --- 首页面板 ---
  UnHomePanel := TPanel.Create(UninstallProgressForm);
  UnHomePanel.Parent := UninstallProgressForm;
  UnHomePanel.SetBounds(0, 0, 900, 524);
  UnHomePanel.BevelOuter := bvNone;
  UnHomePanel.ParentBackground := True;
  UnHomePanel.Visible := True;

  // 标题
  UnTitleLabel := TLabel.Create(UnHomePanel);
  UnTitleLabel.Parent := UnHomePanel;
  UnTitleLabel.SetBounds(0, 120, 900, 120);
  UnTitleLabel.AutoSize := False;
  UnTitleLabel.Alignment := taCenter;
  UnTitleLabel.Caption := 'PyStart';
  UnTitleLabel.Font.Name := 'Segoe UI';
  UnTitleLabel.Font.Size := 48;
  UnTitleLabel.Font.Style := [fsBold];
  UnTitleLabel.Font.Color := clWhite;
  UnTitleLabel.Transparent := True;

  // 快速卸载按钮
  UnQuickBtn := TPanel.Create(UnHomePanel);
  UnQuickBtn.Parent := UnHomePanel;
  UnQuickBtn.SetBounds((900 - 320) div 2, 280, 320, 65);
  UnQuickBtn.Color := $0012C4FF;
  UnQuickBtn.ParentBackground := False;
  UnQuickBtn.BevelOuter := bvNone;
  UnQuickBtn.Cursor := crHand;
    UnQuickBtn.OnClick := @UnQuickBtnClick;
    ApplyRoundedCorners(UnQuickBtn, 30);
  
    UnQuickBtnText := TLabel.Create(UnQuickBtn);
    UnQuickBtnText.Parent := UnQuickBtn;
    UnQuickBtnText.Caption := GetUnText('QuickUninstall');
    UnQuickBtnText.Font.Name := 'Microsoft YaHei UI';
    UnQuickBtnText.Font.Size := 20;
    UnQuickBtnText.Font.Style := [fsBold];
    UnQuickBtnText.Font.Color := $002D2D2D;
    UnQuickBtnText.Alignment := taCenter;
    UnQuickBtnText.AutoSize := False;
    UnQuickBtnText.SetBounds(0, 10, 320, 50);
    UnQuickBtnText.Cursor := crHand;
    UnQuickBtnText.OnClick := @UnQuickBtnClick;
    UnQuickBtnText.Transparent := True;

  // --- 进度面板 ---
  UnProgressPanel := TPanel.Create(UninstallProgressForm);
  UnProgressPanel.Parent := UninstallProgressForm;
  UnProgressPanel.SetBounds(0, 0, 900, 524);
  UnProgressPanel.BevelOuter := bvNone;
  UnProgressPanel.ParentBackground := True;
  UnProgressPanel.Visible := False;

  // 标题 (进度页面)
  UnProgressTitleLabel := TLabel.Create(UnProgressPanel);
  UnProgressTitleLabel.Parent := UnProgressPanel;
  UnProgressTitleLabel.SetBounds(0, 120, 900, 120);
  UnProgressTitleLabel.AutoSize := False;
  UnProgressTitleLabel.Alignment := taCenter;
  UnProgressTitleLabel.Caption := 'PyStart';
  UnProgressTitleLabel.Font.Name := 'Segoe UI';
  UnProgressTitleLabel.Font.Size := 48;
  UnProgressTitleLabel.Font.Style := [fsBold];
  UnProgressTitleLabel.Font.Color := clWhite;
  UnProgressTitleLabel.Transparent := True;

  UnStatusLabel := TLabel.Create(UnProgressPanel);
  UnStatusLabel.Parent := UnProgressPanel;
  UnStatusLabel.SetBounds(150, 300, 600, 30);
  UnStatusLabel.AutoSize := False;
  UnStatusLabel.Alignment := taCenter;
  UnStatusLabel.Font.Name := 'Microsoft YaHei UI';
  UnStatusLabel.Font.Size := 14;
  UnStatusLabel.Font.Color := clWhite;
  UnStatusLabel.Transparent := True;
  UnStatusLabel.Visible := False;

  UninstallProgressForm.StatusLabel.Visible := False;

  UninstallProgressForm.ProgressBar.Parent := UnProgressPanel;
  UninstallProgressForm.ProgressBar.SetBounds(150, 340, 600, 12);
  UninstallProgressForm.ProgressBar.Visible := False;

  // 为每个面板添加关闭按钮，确保点击有效
  UnCloseBtn := TLabel.Create(UnHomePanel);
  UnCloseBtn.Parent := UnHomePanel;
  UnCloseBtn.Caption := '×';
  UnCloseBtn.Font.Name := 'Arial';
  UnCloseBtn.Font.Size := 24;
  UnCloseBtn.Font.Color := clWhite;
  UnCloseBtn.Transparent := True;
  UnCloseBtn.Cursor := crHand;
  UnCloseBtn.Alignment := taCenter;
  UnCloseBtn.SetBounds(UnHomePanel.ClientWidth - 50, 10, 40, 40);
  UnCloseBtn.OnClick := @UnCloseBtnClick;

  UnCloseBtn := TLabel.Create(UnProgressPanel);
  UnCloseBtn.Parent := UnProgressPanel;
  UnCloseBtn.Caption := '×';
  UnCloseBtn.Font.Name := 'Arial';
  UnCloseBtn.Font.Size := 24;
  UnCloseBtn.Font.Color := clWhite;
  UnCloseBtn.Transparent := True;
  UnCloseBtn.Cursor := crHand;
  UnCloseBtn.Alignment := taCenter;
  UnCloseBtn.SetBounds(UnProgressPanel.ClientWidth - 50, 10, 40, 40);
  UnCloseBtn.OnClick := @UnCloseBtnClick;
end;

procedure AppProcessMessage;
var
  Msg: TMsg;
begin
  while PeekMessage(Msg, 0, 0, 0, 1) do
  begin
    TranslateMessage(Msg);
    DispatchMessage(Msg);
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    // 循环等待用户点击“快速卸载”或关闭窗口
    // 注意：即使在静默模式下也要等待，因为我们手动显示了 UI
    while (not CanUninstall) and (not IsAborted) do
    begin
      AppProcessMessage;
      Sleep(10);
    end;
    
    // 如果用户点击了“x”或按了 ESC，则关闭窗口
    if IsAborted then
    begin
      UninstallProgressForm.Close;
      ExitProcess(0);
    end;
  end;

  if CurUninstallStep = usPostUninstall then
  begin
    UnFinished := True;
    // 在卸载完成后，如果窗体还在，则尝试更新语言，但要非常小心
    if (UninstallProgressForm <> nil) and UninstallProgressForm.Visible then
    begin
      RefreshUninstallLanguage();
    end;
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  WizardForm.NextButton.Visible := False;
  WizardForm.BackButton.Visible := False;
  // 保持取消按钮在屏幕外但可见且启用，以确保事件触发
  WizardForm.CancelButton.SetBounds(-100, -100, 0, 0);
  WizardForm.CancelButton.Visible := True;
  WizardForm.CancelButton.Enabled := True;
  WizardForm.Bevel.Visible := False;

  if CurPageID = wpFinished then
  begin
    // 保持 800x600 尺寸，不再缩小
    LogoImage.Visible := False;
    TitleLabel.Visible := False;
    InstallBtn.Visible := False;
    AgreementCheck.Visible := False;
    CustomOptionsLabel.Visible := False;
    PathLabel.Visible := False;
    PathEditPanel.Visible := False;
    BrowseBtn.Visible := False;
    ShortcutCheck.Visible := False;
    LangComboPanel.Visible := False;
    ProgressBar.Visible := False;
    StatusLabel.Visible := False;

    FinishedLabel.Visible := True;
    LaunchCheck.Visible := True;
    FinishBtn.Visible := True;
    WizardForm.ActiveControl := WizardForm.CancelButton;
  end;
end;
