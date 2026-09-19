#!/usr/bin/env bash
# ==============================================================================
# ERPNext & Logistics Wizard - Backup & Restore Manager
# Tự động sao lưu và phục hồi cơ sở dữ liệu, DocTypes, tệp tin và cấu hình
# ==============================================================================

set -e

# Màu sắc giao diện terminal
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

SITE_NAME="logistics.local"
DB_ROOT_PASSWORD="admin"
BACKUP_DIR="$(pwd)/backups"
LATEST_DIR="$BACKUP_DIR/latest"

mkdir -p "$BACKUP_DIR" "$LATEST_DIR"

# Kiểm tra container backend
check_container() {
    local cid
    cid=$(docker compose ps -q backend 2>/dev/null || true)
    if [ -z "$cid" ]; then
        echo -e "${YELLOW}⚠️  Container 'backend' chưa chạy.${NC}"
        read -p "Bạn có muốn khởi động hệ thống bằng 'docker compose up -d' ngay bây giờ không? (y/n): " start_ans
        if [[ "$start_ans" =~ ^[Yy]$ ]]; then
            docker compose up -d
            echo -e "${CYAN}⏳ Đang đợi backend sẵn sàng (10s)...${NC}"
            sleep 10
        else
            echo -e "${RED}❌ Không thể tiếp tục nếu container backend chưa chạy.${NC}"
            exit 1
        fi
    fi
}

# ==============================================================================
# CHỨC NĂNG 1: SAO LƯU (BACKUP)
# ==============================================================================
do_backup() {
    check_container
    local timestamp
    timestamp=$(date +"%Y%m%d_%H%M%S")
    local target_backup_dir="$BACKUP_DIR/backup_$timestamp"

    echo ""
    echo -e "${BLUE}${BOLD}=====================================================${NC}"
    echo -e "${GREEN}${BOLD}💾 BẮT ĐẦU SAO LƯU TOÀN BỘ HỆ THỐNG (BACKUP)${NC}"
    echo -e "${BLUE}${BOLD}=====================================================${NC}"
    echo -e "${CYAN}Site:${NC} $SITE_NAME"
    echo -e "${CYAN}Thời gian sao lưu:${NC} $timestamp"
    echo -e "${CYAN}Thư mục đích trên host:${NC} $target_backup_dir"
    echo ""

    echo -e "${CYAN}1/4. Đang xuất Database, DocTypes và Tệp tin từ container...${NC}"
    docker compose exec -T backend bench --site "$SITE_NAME" backup --with-files

    echo -e "${CYAN}2/4. Đang xác định tệp sao lưu mới nhất trong container...${NC}"
    local files_meta
    files_meta=$(docker compose exec -T backend bash -c '
        LATEST_SQL=$(ls -t sites/logistics.local/private/backups/*-database.sql.gz 2>/dev/null | head -n 1)
        LATEST_PUB=$(ls -t sites/logistics.local/private/backups/*-files.tar 2>/dev/null | head -n 1)
        LATEST_PRIV=$(ls -t sites/logistics.local/private/backups/*-private-files.tar 2>/dev/null | head -n 1)
        LATEST_CONF=$(ls -t sites/logistics.local/private/backups/*-site_config_backup.json 2>/dev/null | head -n 1)
        echo "$LATEST_SQL|$LATEST_PUB|$LATEST_PRIV|$LATEST_CONF"
    ')

    IFS='|' read -r sql_file pub_file priv_file conf_file <<< "$files_meta"

    # Làm sạch ký tự \r nếu có
    sql_file=$(echo "$sql_file" | tr -d '\r\n')
    pub_file=$(echo "$pub_file" | tr -d '\r\n')
    priv_file=$(echo "$priv_file" | tr -d '\r\n')
    conf_file=$(echo "$conf_file" | tr -d '\r\n')

    if [ -z "$sql_file" ]; then
        echo -e "${RED}❌ Không tìm thấy tệp database backup trong container!${NC}"
        exit 1
    fi

    mkdir -p "$target_backup_dir"

    local backend_cid
    backend_cid=$(docker compose ps -q backend)

    echo -e "${CYAN}3/4. Đang sao chép bản sao lưu ra máy host (${target_backup_dir})...${NC}"
    [ -n "$sql_file" ] && docker cp "$backend_cid:/home/frappe/frappe-bench/$sql_file" "$target_backup_dir/database.sql.gz"
    [ -n "$pub_file" ] && docker cp "$backend_cid:/home/frappe/frappe-bench/$pub_file" "$target_backup_dir/files.tar"
    [ -n "$priv_file" ] && docker cp "$backend_cid:/home/frappe/frappe-bench/$priv_file" "$target_backup_dir/private-files.tar"
    [ -n "$conf_file" ] && docker cp "$backend_cid:/home/frappe/frappe-bench/$conf_file" "$target_backup_dir/site_config_backup.json"

    echo -e "${CYAN}4/4. Đang đồng bộ bản 'latest' để đồng đội có thể tự động sử dụng...${NC}"
    rm -rf "$LATEST_DIR"/*
    cp -rf "$target_backup_dir"/* "$LATEST_DIR/"

    # Tạo tệp thông tin tóm tắt
    cat << EOF > "$target_backup_dir/backup_info.txt"
Bản sao lưu: backup_$timestamp
Thời gian tạo: $(date)
Site: $SITE_NAME
Database dump: database.sql.gz ($(du -h "$target_backup_dir/database.sql.gz" | cut -f1))
Tệp công khai: files.tar ($(du -h "$target_backup_dir/files.tar" 2>/dev/null | cut -f1 || echo "0"))
Tệp riêng tư: private-files.tar ($(du -h "$target_backup_dir/private-files.tar" 2>/dev/null | cut -f1 || echo "0"))
EOF
    cp "$target_backup_dir/backup_info.txt" "$LATEST_DIR/backup_info.txt"

    echo ""
    echo -e "${GREEN}${BOLD}✅ SAO LƯU THÀNH CÔNG!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "📁 Thư mục lưu bản snapshot này: ${BOLD}$target_backup_dir${NC}"
    echo -e "⭐ Đã cập nhật bản mặc định:     ${BOLD}$LATEST_DIR${NC}"
    echo -e "📊 Dung lượng Database:          ${BOLD}$(du -h "$target_backup_dir/database.sql.gz" | cut -f1)${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}💡 Mẹo: Khi bạn commit thư mục ${BOLD}backups/latest/${NC}${YELLOW} lên Git, bất kỳ đồng đội nào clone về và chạy Docker cũng sẽ có chính xác dữ liệu của bản sao lưu này!${NC}"
    echo ""
}

# ==============================================================================
# CHỨC NĂNG 2: PHỤC HỒI / GHI ĐÈ (RESTORE)
# ==============================================================================
do_restore() {
    check_container

    echo ""
    echo -e "${BLUE}${BOLD}=====================================================${NC}"
    echo -e "${YELLOW}${BOLD}🔄 PHỤC HỒI / GHI ĐÈ DỮ LIỆU VÀO HỆ THỐNG (RESTORE)${NC}"
    echo -e "${BLUE}${BOLD}=====================================================${NC}"

    # Liệt kê các bản backup có sẵn
    local backups=()
    if [ -f "$LATEST_DIR/database.sql.gz" ]; then
        backups+=("latest")
    fi

    for dir in "$BACKUP_DIR"/backup_*; do
        if [ -d "$dir" ] && [ -f "$dir/database.sql.gz" ]; then
            backups+=("$(basename "$dir")")
        fi
    done

    if [ ${#backups[@]} -eq 0 ]; then
        echo -e "${RED}❌ Không tìm thấy bản sao lưu nào trong thư mục '$BACKUP_DIR'!${NC}"
        echo -e "Vui lòng chọn chức năng (1) để tạo bản sao lưu trước."
        exit 1
    fi

    echo "Danh sách các bản sao lưu hiện có:"
    for i in "${!backups[@]}"; do
        local bname="${backups[$i]}"
        local bpath="$BACKUP_DIR/$bname"
        local bsize
        bsize=$(du -h "$bpath/database.sql.gz" 2>/dev/null | cut -f1 || echo "N/A")
        if [ "$bname" = "latest" ]; then
            echo -e "  [${GREEN}$((i+1))${NC}] ${BOLD}$bname${NC} (Bản sao lưu mới nhất) - Dung lượng DB: $bsize"
        else
            echo -e "  [${CYAN}$((i+1))${NC}] $bname - Dung lượng DB: $bsize"
        fi
    done
    echo ""

    read -p "Chọn số thứ tự bản sao lưu muốn phục hồi [mặc định 1]: " sel_idx
    sel_idx=${sel_idx:-1}

    # Kiểm tra tính hợp lệ của lựa chọn
    if ! [[ "$sel_idx" =~ ^[0-9]+$ ]] || [ "$sel_idx" -lt 1 ] || [ "$sel_idx" -gt ${#backups[@]} ]; then
        echo -e "${RED}❌ Lựa chọn không hợp lệ.${NC}"
        exit 1
    fi

    local chosen_backup="${backups[$((sel_idx-1))]}"
    local src_dir="$BACKUP_DIR/$chosen_backup"

    echo ""
    echo -e "${RED}${BOLD}⚠️  CẢNH BÁO NGUY HIỂM:${NC}"
    echo -e "${YELLOW}Thao tác này sẽ ${RED}${BOLD}GHI ĐÈ HOÀN TOÀN${NC}${YELLOW} cơ sở dữ liệu, danh sách DocType và các tệp tin hiện tại trên site '${BOLD}$SITE_NAME${NC}${YELLOW}' bằng bản sao lưu '${BOLD}$chosen_backup${NC}${YELLOW}'.${NC}"
    read -p "Bạn có chắc chắn 100% muốn thực hiện phục hồi không? (Gõ 'yes' để xác nhận): " confirm_ans

    if [ "$confirm_ans" != "yes" ]; then
        echo -e "${YELLOW}Đã hủy thao tác phục hồi.${NC}"
        exit 0
    fi

    echo ""
    echo -e "${CYAN}1/4. Đang nạp các tệp sao lưu từ máy host vào container...${NC}"
    local backend_cid
    backend_cid=$(docker compose ps -q backend)

    docker compose exec -T backend mkdir -p /tmp/restore_staging
    docker cp "$src_dir/database.sql.gz" "$backend_cid:/tmp/restore_staging/database.sql.gz"
    [ -f "$src_dir/files.tar" ] && docker cp "$src_dir/files.tar" "$backend_cid:/tmp/restore_staging/files.tar"
    [ -f "$src_dir/private-files.tar" ] && docker cp "$src_dir/private-files.tar" "$backend_cid:/tmp/restore_staging/private-files.tar"

    echo -e "${CYAN}2/4. Đang thực thi ghi đè database vào MariaDB (bench restore)...${NC}"
    docker compose exec -T backend bash -c '
        RESTORE_CMD="bench --site '$SITE_NAME' restore /tmp/restore_staging/database.sql.gz --mariadb-root-password '$DB_ROOT_PASSWORD' --force"
        [ -f /tmp/restore_staging/files.tar ] && RESTORE_CMD="$RESTORE_CMD --with-public-files /tmp/restore_staging/files.tar"
        [ -f /tmp/restore_staging/private-files.tar ] && RESTORE_CMD="$RESTORE_CMD --with-private-files /tmp/restore_staging/private-files.tar"
        $RESTORE_CMD
    '

    echo -e "${CYAN}3/4. Đang chạy bench migrate để đồng bộ lại DocTypes và cấu trúc bảng...${NC}"
    docker compose exec -T backend bench --site "$SITE_NAME" migrate

    echo -e "${CYAN}4/4. Đang xóa bộ nhớ đệm (clear-cache) và dọn dẹp tệp tạm...${NC}"
    docker compose exec -T backend bench --site "$SITE_NAME" clear-cache
    docker compose exec -T backend rm -rf /tmp/restore_staging

    echo ""
    echo -e "${GREEN}${BOLD}=====================================================${NC}"
    echo -e "${GREEN}${BOLD}🎉 PHỤC HỒI VÀ GHI ĐÈ DỮ LIỆU THÀNH CÔNG!${NC}"
    echo -e "${GREEN}${BOLD}=====================================================${NC}"
    echo -e "Hệ thống đã được cập nhật chính xác theo bản sao lưu: ${BOLD}$chosen_backup${NC}"
    echo -e "Bạn có thể truy cập ngay: ${CYAN}http://localhost:2828${NC}"
    echo ""
}

# ==============================================================================
# MENU CHÍNH
# ==============================================================================
show_menu() {
    clear 2>/dev/null || true
    echo -e "${BLUE}${BOLD}===================================================================${NC}"
    echo -e "${CYAN}${BOLD}   TRÌNH QUẢN LÝ SAO LƯU & PHỤC HỒI (BACKUP & RESTORE MANAGER)    ${NC}"
    echo -e "${BLUE}${BOLD}===================================================================${NC}"
    echo -e "  ${GREEN}1)${NC} ${BOLD}💾 SAO LƯU (Backup)${NC}  - Lưu toàn bộ Database, DocTypes, tệp & cấu hình"
    echo -e "  ${YELLOW}2)${NC} ${BOLD}🔄 PHỤC HỒI (Restore)${NC} - Ghi đè toàn bộ dữ liệu ra hệ thống hiện tại"
    echo -e "  ${RED}3)${NC} 🚪 Thoát"
    echo -e "${BLUE}${BOLD}===================================================================${NC}"
    echo ""
    read -p "Vui lòng chọn thao tác [1-3]: " choice

    case "$choice" in
        1)
            do_backup
            ;;
        2)
            do_restore
            ;;
        3|q|Q)
            echo "Tạm biệt!"
            exit 0
            ;;
        *)
            echo -e "${RED}Lựa chọn không hợp lệ. Vui lòng chọn 1, 2 hoặc 3.${NC}"
            exit 1
            ;;
    esac
}

# Hỗ trợ truyền tham số trực tiếp (ví dụ: ./backup_manager.sh 1 hoặc ./backup_manager.sh backup)
if [ "$1" = "1" ] || [ "$1" = "backup" ]; then
    do_backup
elif [ "$2" = "2" ] || [ "$1" = "2" ] || [ "$1" = "restore" ]; then
    do_restore
else
    show_menu
fi
