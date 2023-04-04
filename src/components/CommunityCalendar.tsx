import React, { useState } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import icalendarPlugin from "@fullcalendar/icalendar";
import CalendarModal from "./CalendarModal";

const CommunityCalendar: React.FunctionComponent = () => {
    const [showModal, setShowModal] = useState(false);
    const [calendarEvent, setCalendarEvent] = useState();

    const showEventInfo = (info) => {
        setShowModal(!showModal);
        setCalendarEvent(info.event);
    };

    return (
        <>
            <FullCalendar
                slotDuration="00:15:00"
                slotMinTime="09:00:00"
                slotMaxTime="18:00:00"
                navLinks={true}
                nowIndicator={true}
                height={"auto"}
                expandRows={false}
                eventClick={(info) => showEventInfo(info)}
                plugins={[
                    dayGridPlugin,
                    timeGridPlugin,
                    icalendarPlugin,
                    interactionPlugin,
                ]}
                initialView="timeGridWeek"
                weekends={false}
                events={{
                    url: "https://sovereigncloudstack.github.io/calendar/scs.ics",
                    format: "ics",
                }}
                headerToolbar={{
                    left: "prev,next today",
                    center: "title",
                    right: "timeGridDay,timeGridWeek,dayGridMonth",
                }}
            />
            <div>
                <CalendarModal
                    show={showModal}
                    calendarEvent={calendarEvent}
                    onClose={() => setShowModal(false)}
                />
            </div>
        </>
    );
};

export default CommunityCalendar;
