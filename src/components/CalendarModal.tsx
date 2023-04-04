import { preventDefault } from "@fullcalendar/core/internal";
import React from "react";
import Button from "./Button";
import styles from "./calendarModal.module.css";

interface CalendarModalProps {
    calendarEvent: any;
    onClose: () => void;
    show: boolean;
}

const CalendarModal: React.FunctionComponent<CalendarModalProps> = (props) => {
    const { calendarEvent, onClose, show } = props;

    const joinEvent = (e) => {
        e.stopPropagation();
    };

    return (
        <>
            {show && calendarEvent && (
                <div className={styles.modal} onClick={onClose}>
                    <div className={styles.modalContent}>
                        <div className={styles.modalTitle}>
                            <h2 className={styles.modalH2}>
                                {calendarEvent.title}
                            </h2>
                        </div>
                        <div className={styles.modalDescription}>
                            <p>{calendarEvent.extendedProps.description}</p>
                            <p>{calendarEvent.extendedProps.location}</p>
                            <div className={styles.buttonBox}>
                                <Button
                                    handleClick={joinEvent}
                                    title="Join Meeting"
                                    href={calendarEvent.extendedProps.location}
                                />
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default CalendarModal;
